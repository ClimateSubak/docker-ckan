import logging

from ckan import authz, model

log = logging.getLogger(__name__)


def user_list(context, data_dict=None):
    """
    Check whether access to the user list is authorised.
    Restricted to organisation admins.
    """
    return {"success": _requester_is_admin(context)}


def user_show(context, data_dict):
    """
    Check whether access to individual user details is authorised.
    Restricted to organisation admins or self.
    """
    if _requester_is_admin(context):
        return {"success": True}

    requester = context.get("user")
    id = data_dict.get("id", None)
    if id:
        user_obj = model.User.get(id)
    else:
        user_obj = data_dict.get("user_obj", None)
    if user_obj:
        return {"success": requester == user_obj.name}

    return {"success": False}


def _requester_is_admin(context):
    """
    Check whether the current user has admin privileges in some group
    or organisation. This is based on the 'update' privilege; see e.g.
    ckan.logic.auth.update.group_edit_permissions.
    """
    requester = context.get("user")
    return _has_user_permission_for_some_group(requester, "admin")


def _has_user_permission_for_some_group(user_name, permission):
    """
    Check if the user has the given permission for any group.
    """
    user_id = authz.get_user_id_for_username(user_name, allow_none=True)
    if not user_id:
        return False

    roles = authz.get_roles_with_permission(permission)
    if not roles:
        return False

    # get any groups the user has with the needed role
    q = (
        model.Session.query(model.Member)
        .filter(model.Member.table_name == "user")
        .filter(model.Member.state == "active")
        .filter(model.Member.capacity.in_(roles))
        .filter(model.Member.table_id == user_id)
    )

    group_ids = []
    for row in q.all():
        group_ids.append(row.group_id)

    # if not in any groups has no permissions
    if not group_ids:
        return False

    # see if any of the groups are active
    q = (
        model.Session.query(model.Group)
        .filter(model.Group.state == "active")
        .filter(model.Group.id.in_(group_ids))
    )

    return bool(q.count())
