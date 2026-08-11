def check_data(data,required):
    if data is None:
        return False
    for field, ftype in required:
        if field not in data.keys():
            return False
        if not isinstance(data[field], ftype):
            return False
        if ftype is str and data[field].strip() == '':
            return False
    return True
def check_data_nl(data, required):
    if data is None:
        return False
    found_any = False
    for field, ftype in required:
        if field in data and isinstance(data[field], ftype):
            if ftype is str and data[field].strip() == '':
                continue
            found_any = True
    return found_any
