def api_key(view_func):
    setattr(view_func, 'require_api_key', True)
    return view_func
