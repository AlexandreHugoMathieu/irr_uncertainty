# Created by A. MATHIEU & ChatGPT on 26/02/2025
import os
import inspect
import importlib


def find_modules_in_directory(directory):
    """
    Walk through a given directory and return a list of Python modules (.py).
    """
    modules = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and not file.startswith("_"):
                module_path = os.path.join(root, file)
                module_name = os.path.relpath(module_path, directory).replace(os.sep, ".")[:-3]  # Removes ".py"
                modules.append(module_name)
    return modules


def generate_rst_for_module(directory, module_name):
    """
    Generates an .rst section for a given module with a list of all its functions.
    """
    try:
        # Dynamically import the module
        module = importlib.import_module(f"{directory}.{module_name}")
        functions = inspect.getmembers(module, inspect.isfunction)

        # Initialize the content for the module
        module_rst = f"{module_name}\n"
        module_rst += "=" * len(module_rst.strip()) + "\n\n"
        module_rst += f".. automodule:: {directory}.{module_name}\n\n"

        # Add each function of the module
        for func_name, func in functions:
            if func.__module__ == f"{directory}.{module_name}":  # Ensure the function belongs to the module
                module_rst += f".. autofunction:: {directory}.{module_name}.{func_name}\n"

        return module_rst
    except Exception as e:
        print(f"Error while importing or analyzing the module {module_name}: {e}")
        return ""


def generate_full_rst(directory, output_file="docs/source/content.rst"):
    """
    Walk through all the modules in the given directory, generate a `.rst` file with documentation of the functions.
    """
    modules = find_modules_in_directory(directory)
    rst_content = ""

    for module_name in modules:
        rst_content += generate_rst_for_module(directory, module_name)
        rst_content += "\n\n"  # Spacing between modules

    # Save the `.rst` file
    with open(output_file, "w") as f:
        f.write(rst_content)
    print(f"Documentation successfully generated in the file {output_file}")


# Script usage
if __name__ == "__main__":
    # Directory containing the modules to document
    directory = "pv_uncertainty"  # Ensure this directory points to your code
    modules = find_modules_in_directory(directory)
    module_name = modules[0]

    generate_rst_for_module(directory, module_name)
    generate_full_rst(directory)
