from functools import wraps


'''
create decorator method
'''

'to given only username match with "admin" only to be able to do the task'
def admin_only(func):
    @wraps(func)
    def inner(*args,**kwargs):
        fal = 'Unauthorize permission',400
        if not current_user :
            return fal
        id = current_user.get_id()
        return func(*args,**kwargs) if (id == 1) else fal
    return inner
