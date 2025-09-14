from fastapi.responses import JSONResponse


class ActivityResponse(JSONResponse):
    """Response that ensures the content-type is
    "application/activity+json"
    """

    media_type = "application/activity+json"
