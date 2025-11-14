import h5py

def print_h5_structure(filename):
    def visit(name, obj):
        if isinstance(obj, h5py.Group):
            print(f"[GROUP] {name}")
        elif isinstance(obj, h5py.Dataset):
            print(f"  [DATASET] {name}  shape={obj.shape}  dtype={obj.dtype}")

    with h5py.File(filename, 'r') as f:
        f.visititems(visit)

def print_group_data(filename, group_name):
    def print_items(name, obj, indent=0):
        prefix = "  " * indent
        if isinstance(obj, h5py.Dataset):
            print(f"{prefix}[DATASET] {name}  shape={obj.shape}  dtype={obj.dtype}")
            print(f"{prefix}  Data: {obj[...]}")
        elif isinstance(obj, h5py.Group):
            print(f"{prefix}[GROUP] {name}")
            for sub_name, sub_obj in obj.items():
                print_items(sub_name, sub_obj, indent + 1)

    with h5py.File(filename, 'r') as f:
        if group_name in f:
            print_items(group_name, f[group_name])
        else:
            print(f"Group '{group_name}' not found in the file.")


# Example usage
var = "./LiveX_Demo_0013_furnace.h5"
print_h5_structure(var)
print_group_data(var, 'event_data')
