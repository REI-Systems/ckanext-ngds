from ckan.plugins.toolkit import toolkit
from ckanext.ngds.base.controllers.ngds_crud_controller import NgdsCrudController

def dispatch(context, data_dict):
    """
    Send the action request to the correct place, based on the POST body
    
    Body should contain JSON data as follows:
    {
      "model": One of BulkUpload
      "process": One of "create", "read", "update", "delete"
      "data": An object containing the data to act on
    }
    
    Requests are inspected and passed on to model-specific controllers, defined below
    
    """
    
    # Determine the correct controller by inspecting the data_dict
    request_model = data_dict.get("model", None)
    controller = None
    if request_model == "BulkUpload":
        controller = BulkUploadController(context)
    else:
        raise toolkit.ValidationError({}, "Please supply a 'model' attribute in the POST body. Value can be one of: BulkUpload")
    
    # execute method inspects POST body and runs the correct functions
    return controller.execute(data_dict)

class BulkUploadController(NgdsCrudController):
    """Controls CRUD API for BulkUpload"""
    def __init__(self, context):
        """Find the right model for this class"""
        self.model = context['model'].BulkUpload