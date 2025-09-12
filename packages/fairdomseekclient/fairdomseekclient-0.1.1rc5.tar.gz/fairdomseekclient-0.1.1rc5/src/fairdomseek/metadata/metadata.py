import importlib
import logging
import pkgutil

from fairdomseek.app_context import FairdomSeekContext
from fairdomseek.types.assay import Assay
from fairdomseek.types.attribute import AttrType
from fairdomseek.types.base_types import People, Project, Institution, Public
from fairdomseek.types.extension import Extension
from fairdomseek.types.investigation import Investigation
from fairdomseek.types.sample_type import SampleType
from fairdomseek.types.study import Study
from fairdomseek.util.topology import order_st_processing
from openapi_client import ApiClient, ExtendedMetadataTypesApi

LOGGER = logging.getLogger(__name__)


class Metadata:

    def __init__(self, project_name=""):
        # Injected objects
        self.sample_types = []
        self.extensions = []
        self.actors = []
        self.investigations = []
        self.studies = []
        self.assays = []
        self.project_name =project_name

        self.fs_ctx = FairdomSeekContext()

    def _add_object(self, obj):
        if isinstance(obj, Extension):
            self.extensions.append(obj)
            return
        if isinstance(obj, SampleType):
            self.sample_types.append(obj)
            return
        if isinstance(obj, People) or isinstance(obj, Project) or \
                isinstance(obj, Institution) or isinstance(obj, Public):
            self.actors.append(obj)
            return
        if isinstance(obj, Investigation):
            self.investigations.append(obj)
            return
        if isinstance(obj, Study):
            self.studies.append(obj)
            return
        if isinstance(obj, Assay):
            self.assays.append(obj)
            return


    def load_package(self, package_name):
        def recursive_import(package):
            for finder, modname, ispkg in pkgutil.iter_modules(package.__path__):
                full_modname = f"{package.__name__}.{modname}"
                submodule = importlib.import_module(full_modname)

                # Recurse if it's a subpackage
                if ispkg:
                    recursive_import(submodule)

        imported_package = importlib.import_module(package_name)
        recursive_import(imported_package)

        LOGGER.info("******************************")
        LOGGER.info("Following sample type(s) found: {}".format(', '.join([st.title for st in self.sample_types])))
        LOGGER.info("Following investigation(s) found: {}".format(', '.join([iv.title for iv in self.investigations])))
        LOGGER.info("Following studi(es) found: {}".format(', '.join([std.title for std in self.studies])))
        LOGGER.info("Following involved actor(s) found: {}".format(', '.join([a.id() for a in self.actors])))
        LOGGER.info("******************************\n")

    def create_all(self, fairdom_seek_client: ApiClient, auto_delete=False):
        # Setting clients and project name on all services
        self.fs_ctx.set_client(fairdom_seek_client)
        self.fs_ctx.set_project_name(self.project_name)

        # self._manage_extensions(auto_delete)
        i_c, i_u, i_d = self._manage_investigation(auto_delete)
        s_c, s_u, s_d = self._manage_studies(auto_delete)
        st_c, st_u, st_d = self._manage_sample_types(auto_delete)

        # Create everything first
        for iv in i_c:
            LOGGER.info("Creating investigation {} ...".format(iv.title))
            try:
                self._create_investigation(iv)
                LOGGER.info("... OK".format(iv.title))
            except Exception as e:
                LOGGER.error("Can't create investigation: {}".format(str(e)))
        for st in s_c:
            LOGGER.info("Creating study {} ...".format(st.title))
            try:
                self._create_study(st)
                LOGGER.info("... OK".format(st.title))
            except Exception as e:
                LOGGER.error("Can't create study: {}".format(str(e)))
        for st_c in st_c:
            LOGGER.info("Creating sample type {} ...".format(st_c.title))
            try:
                self._create_sample_type(st_c)
                LOGGER.info("... OK".format(st_c.title))
            except Exception as e:
                LOGGER.error("Can't create sample type: {}".format(str(e)))

        # Then update what needs to be updated
        for iv in i_u:
            LOGGER.info("Checking investigation {}  for update ...".format(iv[0].title))
            self._update_investigation(iv[0], iv[1])
            LOGGER.info("... OK")

        for st in s_u:
            LOGGER.info("Checking study {}  for update ...".format(st[0].title))
            self._update_study(st[0], st[1])
            LOGGER.info("... OK")

        for st_c in st_u:
            LOGGER.info("Checking sample type {}  for update ...".format(st_c[0].title))
            self._update_sample_type(st_c[0], st_c[1])
            LOGGER.info("... OK")

        # Finally delete, eventually, reverse order from creation
        if auto_delete is True:
            # Study, investigation, sample, and then sample types
            for st in s_d:
                try:
                    LOGGER.info("Deleting study {}...".format(st.title))
                    self._delete_study(st.external_id)
                    LOGGER.info("... OK".format(st.title))
                except Exception as e:
                    LOGGER.error("Can't delete study {}: {}".format(st.title, e))

            for iv in i_d:
                try:
                    LOGGER.info("Deleting investigation {}...".format(iv.title))
                    self._delete_investigation(iv.external_id)
                    LOGGER.info("... OK".format(iv.title))
                except Exception as e:
                    LOGGER.error("Can't delete investigation {}:{}".format(iv.title, e))

            for st in st_d:
                try:
                    LOGGER.info("Deleting sample type {}...".format(st.title))
                    self._delete_sample_type(st.external_id)
                    LOGGER.info("... OK".format(st.title))
                except Exception as e:
                    LOGGER.error("Can't delete sample type {}: {}".format(st.title, e))

    def _manage_extensions(self, client, auto_delete):
        # Retrieve all extension
        LOGGER.warning("NOT IMPLEMENTED")

    def _manage_investigation(self, auto_delete):

        to_create, to_update, to_delete = [], [], []
        # Retrieving all investigations from the project
        LOGGER.debug("Fetching existing investigations from {} project...".format(self.fs_ctx.project_name))
        remote_investigations = self.fs_ctx.investigations_service().list_investigations_by_title()
        LOGGER.debug("... OK".format(self.fs_ctx.project_name))

        # Check if sample type already exists (not enforced by the backend, but title is considered unique in the project scope to avoid duplication)
        for iv in self.investigations:
            if iv.title in remote_investigations.keys():
                to_update.append((remote_investigations[iv.title], iv))
            else:
                to_create.append(iv)

        # Eventually delete sample type
        if auto_delete:
            for iv_title in remote_investigations.keys():
                if iv_title not in [iv.title for iv in self.investigations]:
                    to_delete.append(remote_investigations[iv_title])

        return to_create, to_update, to_delete

    def _create_investigation(self, iv):
        return self.fs_ctx.investigations_service().create_investigation(iv)

    def _update_investigation(self, remote_iv, local_iv):
        if remote_iv != local_iv:
            LOGGER.info("Updating {}".format(remote_iv.title))
            return self.fs_ctx.investigations_service().patch_investigation(remote_iv, local_iv)
        else:
            LOGGER.info("{} didn't change, no update needed".format(local_iv.title))
            return "ok"

    def _delete_investigation(self, investigation_id):
        self.fs_ctx.investigations_service().delete_investigation(int(investigation_id))

    def _manage_studies(self, auto_delete):

        to_create, to_update, to_delete = [], [], []
        # Retrieving all studies from the project
        LOGGER.debug("Fetching existing studies from {} project...".format(self.fs_ctx.project_name))
        remote_studies = self.fs_ctx.studies_service().list_studies_by_title()
        LOGGER.debug("... OK".format(self.fs_ctx.project_name))

        # Check if study already exists (not enforced by the backend, but title is considered unique)
        for st in self.studies:
            if st.title in remote_studies.keys():
                to_update.append((remote_studies[st.title], st))
            else:
                to_create.append(st)

        # Eventually delete sample type
        if auto_delete:
            for st_tile in remote_studies.keys():
                if st_tile not in [st.title for st in self.studies]:
                    to_delete.append(remote_studies[st_tile])

        return to_create, to_update, to_delete

    def _create_study(self, st):
        return self.fs_ctx.studies_service().create_study(st)

    def _update_study(self, remote_st, local_st):
        # unsure remote_st has its dependencies is fully solved
        if remote_st.investigation.title is None:
            remote_st.investigation = self.fs_ctx.investigations_service().get_investigation_by_id(int(remote_st.investigation.external_id))
        if remote_st != local_st:
            LOGGER.info("Updating {}".format(remote_st.title))
            return self.fs_ctx.studies_service().patch_study(remote_st, local_st)
        else:
            LOGGER.info("{} didn't change, no update needed".format(local_st.title))
            return "ok"

    def _delete_study(self, study_id):
        self.fs_ctx.studies_service().delete_study(int(study_id))

    def _manage_sample_types(self, auto_delete):

        to_create, to_update, to_delete = [], [], []

        # Retrieving all sample types from the project now
        LOGGER.debug("Fetching existing sample types from {} project...".format(self.fs_ctx.project_name))
        remote_sample_types = self.fs_ctx.sample_types_service().list_sample_types_by_title()
        local_sample_types = [st.title for st in self.sample_types]
        LOGGER.debug("... OK".format(self.fs_ctx.project_name))

        # Check that all referenced sample types are defined remotely or locally
        are_defined = True
        for st in self.sample_types:
            for attr in st.attributes:
                if attr.type == AttrType.RegisteredSample or attr.type == AttrType.RegisteredSampleList:
                    if attr.registered_sample_title not in remote_sample_types and \
                            attr.registered_sample_title not in local_sample_types:
                        LOGGER.error("\"{}\" attribute of \"{}\" sample type references \"{}\" sample type, which does not exist remotely or locally".format(
                            attr.title,
                            st.title,
                            attr.registered_sample_title
                        ))
                        are_defined =False
        if not are_defined:
            exit(-1)

        # Resolve dependency graph here
        for st in order_st_processing(self.sample_types):
            # Check if sample type already exists (not enforced by the backend, but title is considered unique)
            if st.title in remote_sample_types.keys():
                to_update.append((remote_sample_types[st.title], st))
            else:
                to_create.append(st)

        # Eventually delete sample type
        if auto_delete:
            for st_title in remote_sample_types.keys():
                if st_title not in [st.title for st in self.sample_types]:
                    try:
                        LOGGER.info("Deleting sample type {}...".format(st_title))
                        self._delete_sample_type(remote_sample_types[st_title].external_id)
                        to_delete.append(remote_sample_types[st_title])
                        LOGGER.info("... OK".format(st_title))
                    except Exception as e:
                        LOGGER.error("Can't delete sample type {}".format(st_title))

        return to_create, to_update, to_delete

    def _create_sample_type(self, sample_type):
        return self.fs_ctx.sample_types_service().create_sample_type(sample_type)

    def _update_sample_type(self, remote_sample, local_sample):
        if remote_sample != local_sample:
            LOGGER.info("Updating {}".format(local_sample.title))
            return self.fs_ctx.sample_types_service().patch_sample_type(remote_sample, local_sample)
        else:
            LOGGER.info("{} didn't change, no update needed".format(local_sample.title))
            return "ok"

    def _delete_sample_type(self, st_id):
        self.fs_ctx.sample_types_service().delete_sample_type(int(st_id))

