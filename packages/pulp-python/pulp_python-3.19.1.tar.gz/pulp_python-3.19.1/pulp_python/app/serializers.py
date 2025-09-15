import logging
import os
from gettext import gettext as _
from django.conf import settings
from django.db.utils import IntegrityError
from packaging.requirements import Requirement
from rest_framework import serializers

from pulpcore.plugin import models as core_models
from pulpcore.plugin import serializers as core_serializers
from pulpcore.plugin.util import get_domain

from pulp_python.app import models as python_models
from pulp_python.app.utils import (
    DIST_EXTENSIONS,
    artifact_to_python_content_data,
    get_project_metadata_from_file,
    parse_project_metadata,
)


log = logging.getLogger(__name__)


class PythonRepositorySerializer(core_serializers.RepositorySerializer):
    """
    Serializer for Python Repositories.
    """

    autopublish = serializers.BooleanField(
        help_text=_(
            "Whether to automatically create publications for new repository versions, "
            "and update any distributions pointing to this repository."
        ),
        default=False,
        required=False,
    )

    class Meta:
        fields = core_serializers.RepositorySerializer.Meta.fields + ("autopublish",)
        model = python_models.PythonRepository


class PythonDistributionSerializer(core_serializers.DistributionSerializer):
    """
    Serializer for Pulp distributions for the Python type.
    """

    publication = core_serializers.DetailRelatedField(
        required=False,
        help_text=_("Publication to be served"),
        view_name_pattern=r"publications(-.*/.*)?-detail",
        queryset=core_models.Publication.objects.exclude(complete=False),
        allow_null=True,
    )
    base_url = serializers.SerializerMethodField(read_only=True)
    allow_uploads = serializers.BooleanField(
        default=True, help_text=_("Allow packages to be uploaded to this index.")
    )
    remote = core_serializers.DetailRelatedField(
        required=False,
        help_text=_("Remote that can be used to fetch content when using pull-through caching."),
        view_name_pattern=r"remotes(-.*/.*)?-detail",
        queryset=core_models.Remote.objects.all(),
        allow_null=True,
    )

    def get_base_url(self, obj):
        """Gets the base url."""
        if settings.DOMAIN_ENABLED:
            return f"{settings.PYPI_API_HOSTNAME}/pypi/{get_domain().name}/{obj.base_path}/"
        return f"{settings.PYPI_API_HOSTNAME}/pypi/{obj.base_path}/"

    class Meta:
        fields = core_serializers.DistributionSerializer.Meta.fields + (
            "publication",
            "allow_uploads",
            "remote",
        )
        model = python_models.PythonDistribution


class PythonPackageContentSerializer(core_serializers.SingleArtifactContentUploadSerializer):
    """
    A Serializer for PythonPackageContent.
    """

    # Core metadata
    # Version 1.0
    author = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_(
            "Text containing the author's name. Contact information can also be added,"
            " separated with newlines."
        ),
    )
    author_email = serializers.CharField(
        required=False, allow_blank=True, help_text=_("The author's e-mail address. ")
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("A longer description of the package that can run to several paragraphs."),
    )
    home_page = serializers.CharField(
        required=False, allow_blank=True, help_text=_("The URL for the package's home page.")
    )
    keywords = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_(
            "Additional keywords to be used to assist searching for the "
            "package in a larger catalog."
        ),
    )
    license = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("Text indicating the license covering the distribution"),
    )
    metadata_version = serializers.CharField(
        help_text=_("Version of the file format"),
        read_only=True,
    )
    name = serializers.CharField(
        help_text=_("The name of the python project."),
        read_only=True,
    )
    platform = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_(
            "A comma-separated list of platform specifications, "
            "summarizing the operating systems supported by the package."
        ),
    )
    summary = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("A one-line summary of what the package does."),
    )
    version = serializers.CharField(
        help_text=_("The packages version number."),
        read_only=True,
    )
    # Version 1.1
    classifiers = serializers.JSONField(
        required=False,
        default=list,
        help_text=_("A JSON list containing classification values for a Python package."),
    )
    download_url = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("Legacy field denoting the URL from which this package can be downloaded."),
    )
    supported_platform = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("Field to specify the OS and CPU for which the binary package was compiled. "),
    )
    # Version 1.2
    maintainer = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_(
            "The maintainer's name at a minimum; " "additional contact information may be provided."
        ),
    )
    maintainer_email = serializers.CharField(
        required=False, allow_blank=True, help_text=_("The maintainer's e-mail address.")
    )
    obsoletes_dist = serializers.JSONField(
        required=False,
        default=list,
        help_text=_(
            "A JSON list containing names of a distutils project's distribution which "
            "this distribution renders obsolete, meaning that the two projects should not "
            "be installed at the same time."
        ),
    )
    project_url = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("A browsable URL for the project and a label for it, separated by a comma."),
    )
    project_urls = serializers.JSONField(
        required=False,
        default=dict,
        help_text=_("A dictionary of labels and URLs for the project."),
    )
    provides_dist = serializers.JSONField(
        required=False,
        default=list,
        help_text=_(
            "A JSON list containing names of a Distutils project which is contained"
            " within this distribution."
        ),
    )
    requires_external = serializers.JSONField(
        required=False,
        default=list,
        help_text=_(
            "A JSON list containing some dependency in the system that the distribution "
            "is to be used."
        ),
    )
    requires_dist = serializers.JSONField(
        required=False,
        default=list,
        help_text=_(
            "A JSON list containing names of some other distutils project "
            "required by this distribution."
        ),
    )
    requires_python = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_(
            "The Python version(s) that the distribution is guaranteed to be compatible with."
        ),
    )
    # Version 2.1
    description_content_type = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_(
            "A string stating the markup syntax (if any) used in the distribution's"
            " description, so that tools can intelligently render the description."
        ),
    )
    provides_extras = serializers.JSONField(
        required=False,
        default=list,
        help_text=_("A JSON list containing names of optional features provided by the package."),
    )
    # Version 2.2
    dynamic = serializers.JSONField(
        required=False,
        default=list,
        help_text=_(
            "A JSON list containing names of other core metadata fields which are "
            "permitted to vary between sdist and bdist packages. Fields NOT marked "
            "dynamic MUST be the same between bdist and sdist."
        ),
    )
    # Version 2.4
    license_expression = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("Text string that is a valid SPDX license expression."),
    )
    license_file = serializers.JSONField(
        required=False,
        default=list,
        help_text=_("A JSON list containing names of the paths to license-related files."),
    )
    # Release metadata
    filename = serializers.CharField(
        help_text=_(
            "The name of the distribution package, usually of the format:"
            " {distribution}-{version}(-{build tag})?-{python tag}-{abi tag}"
            "-{platform tag}.{packagetype}"
        ),
        read_only=True,
    )
    packagetype = serializers.CharField(
        help_text=_(
            "The type of the distribution package (e.g. sdist, bdist_wheel, bdist_egg, etc)"
        ),
        read_only=True,
    )
    python_version = serializers.CharField(
        help_text=_(
            "The tag that indicates which Python implementation or version the package requires."
        ),
        read_only=True,
    )
    sha256 = serializers.CharField(
        default="",
        help_text=_("The SHA256 digest of this package."),
    )

    def deferred_validate(self, data):
        """
        Validate the python package data.

        Args:
            data (dict): Data to be validated

        Returns:
            dict: Data that has been validated

        """
        data = super().deferred_validate(data)

        try:
            filename = data["relative_path"]
        except KeyError:
            raise serializers.ValidationError(detail={"relative_path": _("This field is required")})

        artifact = data["artifact"]
        try:
            _data = artifact_to_python_content_data(filename, artifact, domain=get_domain())
        except ValueError:
            raise serializers.ValidationError(
                _(
                    "Extension on {} is not a valid python extension "
                    "(.whl, .exe, .egg, .tar.gz, .tar.bz2, .zip)"
                ).format(filename)
            )

        if data.get("sha256") and data["sha256"] != artifact.sha256:
            raise serializers.ValidationError(
                detail={
                    "sha256": _(
                        "The uploaded artifact's sha256 checksum does not match the one provided"
                    )
                }
            )

        data.update(_data)

        return data

    def retrieve(self, validated_data):
        content = python_models.PythonPackageContent.objects.filter(
            sha256=validated_data["sha256"], _pulp_domain=get_domain()
        )
        return content.first()

    class Meta:
        fields = core_serializers.SingleArtifactContentUploadSerializer.Meta.fields + (
            "author",
            "author_email",
            "description",
            "home_page",
            "keywords",
            "license",
            "metadata_version",
            "name",
            "platform",
            "summary",
            "version",
            "classifiers",
            "download_url",
            "supported_platform",
            "maintainer",
            "maintainer_email",
            "obsoletes_dist",
            "project_url",
            "project_urls",
            "provides_dist",
            "requires_external",
            "requires_dist",
            "requires_python",
            "description_content_type",
            "provides_extras",
            "dynamic",
            "license_expression",
            "license_file",
            "filename",
            "packagetype",
            "python_version",
            "sha256",
        )
        model = python_models.PythonPackageContent


class PythonPackageContentUploadSerializer(PythonPackageContentSerializer):
    """
    A serializer for requests to synchronously upload Python packages.
    """

    def validate(self, data):
        """
        Validates an uploaded Python package file, extracts its metadata,
        and creates or retrieves an associated Artifact.

        Returns updated data with artifact and metadata details.
        """
        file = data.pop("file")
        filename = file.name

        for ext, packagetype in DIST_EXTENSIONS.items():
            if filename.endswith(ext):
                break
        else:
            raise serializers.ValidationError(
                _(
                    "Extension on {} is not a valid python extension "
                    "(.whl, .exe, .egg, .tar.gz, .tar.bz2, .zip)"
                ).format(filename)
            )

        # Replace the incorrect file name in the file path with the original file name
        original_filepath = file.file.name
        path_to_file, tmp_str = original_filepath.rsplit("/", maxsplit=1)
        tmp_str = tmp_str.split(".", maxsplit=1)[0]  # Remove e.g. ".upload.gz" suffix
        new_filepath = f"{path_to_file}/{tmp_str}{filename}"
        os.rename(original_filepath, new_filepath)

        metadata = get_project_metadata_from_file(new_filepath)
        artifact = core_models.Artifact.init_and_validate(new_filepath)
        try:
            artifact.save()
        except IntegrityError:
            artifact = core_models.Artifact.objects.get(
                sha256=artifact.sha256, pulp_domain=get_domain()
            )
            artifact.touch()
            log.info(f"Artifact for {file.name} already existed in database")

        data["artifact"] = artifact
        data["sha256"] = artifact.sha256
        data["relative_path"] = filename
        data.update(parse_project_metadata(vars(metadata)))
        # Overwrite filename from metadata
        data["filename"] = filename
        return data

    class Meta(PythonPackageContentSerializer.Meta):
        # This API does not support uploading to a repository or using a custom relative_path
        fields = tuple(
            f
            for f in PythonPackageContentSerializer.Meta.fields
            if f not in ["repository", "relative_path"]
        )
        model = python_models.PythonPackageContent
        # Name used for the OpenAPI request object
        ref_name = "PythonPackageContentUpload"


class MinimalPythonPackageContentSerializer(PythonPackageContentSerializer):
    """
    A Serializer for PythonPackageContent.
    """

    class Meta:
        fields = core_serializers.SingleArtifactContentUploadSerializer.Meta.fields + (
            "filename",
            "packagetype",
            "name",
            "version",
            "sha256",
        )
        model = python_models.PythonPackageContent


class MultipleChoiceArrayField(serializers.MultipleChoiceField):
    """
    A wrapper to make sure this DRF serializer works properly with ArrayFields.
    """

    def to_internal_value(self, data):
        """Converts set to list."""
        return list(super().to_internal_value(data))


class PythonRemoteSerializer(core_serializers.RemoteSerializer):
    """
    A Serializer for PythonRemote.
    """

    includes = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
        required=False,
        allow_empty=True,
        help_text=_("A list containing project specifiers for Python packages to include."),
    )
    excludes = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
        required=False,
        allow_empty=True,
        help_text=_("A list containing project specifiers for Python packages to exclude."),
    )
    prereleases = serializers.BooleanField(
        required=False, help_text=_("Whether or not to include pre-release packages in the sync.")
    )
    policy = serializers.ChoiceField(
        help_text=_(
            "The policy to use when downloading content. The possible values include: "
            "'immediate', 'on_demand', and 'streamed'. 'on_demand' is the default."
        ),
        choices=core_models.Remote.POLICY_CHOICES,
        default=core_models.Remote.ON_DEMAND,
    )
    package_types = MultipleChoiceArrayField(
        required=False,
        help_text=_(
            "The package types to sync for Python content. Leave blank to get every" "package type."
        ),
        choices=python_models.PACKAGE_TYPES,
        default=list,
    )
    keep_latest_packages = serializers.IntegerField(
        required=False,
        help_text=_(
            "The amount of latest versions of a package to keep on sync, includes"
            "pre-releases if synced. Default 0 keeps all versions."
        ),
        default=0,
    )
    exclude_platforms = MultipleChoiceArrayField(
        required=False,
        help_text=_(
            "List of platforms to exclude syncing Python packages for. Possible values"
            "include: windows, macos, freebsd, and linux."
        ),
        choices=python_models.PLATFORMS,
        default=list,
    )

    def validate_includes(self, value):
        """Validates the includes"""
        for pkg in value:
            try:
                Requirement(pkg)
            except ValueError as ve:
                raise serializers.ValidationError(
                    _("includes specifier {} is invalid. {}".format(pkg, ve))
                )
        return value

    def validate_excludes(self, value):
        """Validates the excludes"""
        for pkg in value:
            try:
                Requirement(pkg)
            except ValueError as ve:
                raise serializers.ValidationError(
                    _("excludes specifier {} is invalid. {}".format(pkg, ve))
                )
        return value

    class Meta:
        fields = core_serializers.RemoteSerializer.Meta.fields + (
            "includes",
            "excludes",
            "prereleases",
            "package_types",
            "keep_latest_packages",
            "exclude_platforms",
        )
        model = python_models.PythonRemote


class PythonBanderRemoteSerializer(serializers.Serializer):
    """
    A Serializer for the initial step of creating a Python Remote from a Bandersnatch config file
    """

    config = serializers.FileField(
        help_text=_("A Bandersnatch config that may be used to construct a Python Remote."),
        required=True,
        write_only=True,
    )
    name = serializers.CharField(
        help_text=_("A unique name for this remote"),
        required=True,
    )

    policy = serializers.ChoiceField(
        help_text=_(
            "The policy to use when downloading content. The possible values include: "
            "'immediate', 'on_demand', and 'streamed'. 'on_demand' is the default."
        ),
        choices=core_models.Remote.POLICY_CHOICES,
        default=core_models.Remote.ON_DEMAND,
    )


class PythonPublicationSerializer(core_serializers.PublicationSerializer):
    """
    A Serializer for PythonPublication.
    """

    distributions = core_serializers.DetailRelatedField(
        help_text=_(
            "This publication is currently being hosted as configured by these distributions."
        ),
        source="distribution_set",
        view_name="pythondistributions-detail",
        many=True,
        read_only=True,
    )

    class Meta:
        fields = core_serializers.PublicationSerializer.Meta.fields + ("distributions",)
        model = python_models.PythonPublication
