import os
import ast
from sys import argv,exit

class FunctionVisitor(ast.NodeVisitor):
    def __init__(self):
        self.class_stack = []
        self.function_info = []  # Store (function_path, docstring) tuples

    def visit_ClassDef(self, node):
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node):
        if self.class_stack:
            class_name = ".".join(self.class_stack)
            function_path = f"{class_name}.{node.name}"
        else:
            function_path = node.name

        docstring = ast.get_docstring(node)
        self.function_info.append((function_path, docstring))
        self.generic_visit(node)

def print_directory_tree(root_dir):
    current_class = None
    
    for root, dirs, files in os.walk(root_dir):
        # Print the current directory
        print(f"Directory: {root}")
        
        # Process Python files in the current directory
        for filename in files:
            if filename.endswith('.py'):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    try:
                        tree = ast.parse(file.read())

                        # Create a FunctionVisitor instance and visit the AST
                        visitor = FunctionVisitor()
                        visitor.visit(tree)                        

                        for function_path, docstring in visitor.function_info:
                            if '__init__' not in function_path:
                                print(f"Python File: {filename}")
                                print(f"    Function: {function_path}")
                                print(f"    Docstring: {docstring}\n")
                                print("=========================")

                    except SyntaxError:
                        print(f"    Syntax Error in {filename}")

        print()  # Add an empty line to separate directories

# Example usage: Print the directory tree starting from the current directory
print_directory_tree(argv[1])
