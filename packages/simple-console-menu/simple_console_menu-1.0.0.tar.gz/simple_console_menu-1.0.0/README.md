# Simple Consol Menu
this module allows you to create simple console menu. <br>
[![](https://img.shields.io/pypi/dm/simple-console-menu)](
https://pypi.org/project/simple-console-menu/)

## links
[Source](https://github.com/mikeee1/simple-console-menu) <br>
[Documentation](https://github.com/mikeee1/simple-console-menu/wiki) <br>
[Bug Report](https://github.com/mikeee1/simple-console-menu/issues) <br>
[PyPi](https://pypi.org/project/simple-console-menu/) 

## Installation
```
pip install simple-console-menu
```

## Usage
```python
from simple_console_menu import Menu
```

## Example
```python
from simple_console_menu import Menu

example_menu = Menu.menu("Menu", ["item 1", "item 2", "item 3"])
example_menu.display()
user_input = example_menu.get_user_input()
print(user_input)
```