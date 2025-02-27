def check_matching_crs(
    objects: list,
) -> bool:
    """Check if every object in a list has a crs, and that they match.

    Args:
        objects (list): A list of objects to check.

    Returns:
        bool: True if everything matches, false if not.
    """
    epsg_list = []

    for object in objects:
        if not object.crs:
            return False
        epsg = object.crs.to_epsg()
        epsg_list.append(epsg)

    if len(set(epsg_list)) != 1:
        return False

    return True
