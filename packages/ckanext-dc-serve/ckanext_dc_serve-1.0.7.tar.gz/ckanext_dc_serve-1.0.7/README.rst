ckanext-dc_serve
================

|PyPI Version| |Build Status| |Coverage Status|

This CKAN plugin provides an API for accessing DC data. The python
package dclab implements a client library (``dclab.rtdc_dataset.fmt_dcor``)
to access this API. DCscope offers a GUI via *File - Load DCOR data*.

This plugin implements:

- The DCOR API for accessing DC datasets online (dcserv).
- A background job that generates a condensed dataset after a resource
  has been created.
- A background job that uploads the condensed dataset to the S3 object
  store. The temporary location of the condensed dataset that is created
  can be set by setting the ``ckanext.dc_serve.tmp_dir`` configuration
  option.
- A route that makes the condensed dataset available via
  "/dataset/{id}/resource/{resource_id}/condensed.rtdc"
  (S3 object store data is made available via a redirect)
- A route overriding the default route for downloading a resource via
  "/dataset/{id}/resource/{resource_id}/download/resource_name"
  (S3 object store data is made available via a redirect)
- Extends the template to show a condensed resource download button

- CLI:

  - add CKAN command ``run-jobs-dc-serve`` that runs all background
    jobs for all resources (if not already done)

- Configuration keywords:

  - the ``ckanext.dc_serve.create_condensed_datasets`` boolean
    parameter can be set to False to prevent DCOR from generating condensed
    resource files

  - ``ckanext.dc_serve.enable_intra_dataset_basins`` specifies whether
    intra-dataset basins should be generated or not

  - ``ckanext.dc_serve.tmp_dir`` specifies the location of a directory
    used for creating temporary files when condensing datasets; if not
    specified, a temporary directory is used


Installation
------------

::

    pip install ckanext-dc_serve


Add this extension to the plugins and defaul_views in ckan.ini:

::

    ckan.plugins = [...] dc_serve


Testing
-------
Testing is implemented via GitHub Actions. You may also set up a local
docker container with CKAN and MinIO. Take a look at the GitHub Actions
workflow for more information.


.. |PyPI Version| image:: https://img.shields.io/pypi/v/ckanext.dc_serve.svg
   :target: https://pypi.python.org/pypi/ckanext.dc_serve
.. |Build Status| image:: https://img.shields.io/github/actions/workflow/status/DCOR-dev/ckanext-dc_serve/check.yml
   :target: https://github.com/DCOR-dev/ckanext-dc_serve/actions?query=workflow%3AChecks
.. |Coverage Status| image:: https://img.shields.io/codecov/c/github/DCOR-dev/ckanext-dc_serve
   :target: https://codecov.io/gh/DCOR-dev/ckanext-dc_serve
