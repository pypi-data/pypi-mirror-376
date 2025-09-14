###Singleton Decorator Library

A decorator based on wiki.python.org Python Decorators Library, namely
https://wiki.python.org/moin/PythonDecoratorLibrary#Singleton, with significant
improvements.

Features (assuming you decorate a class definition of MyClass)  
* Every call of MyClass() results in the same instance, which persists from the first instantiation until the end of execution  
* Even if you delete all your references to the instance, it still persists to be returned on the next call of MyClass()  
* That instance is only initiallized once (the first time)  
* is_instance(MyClass(), MyClass) is True (that is, we do not wrap the class)  
* Using copy() or deepcopy() simply gives another reference to the single instance  
* The overhead of locking in the threaded version is low enough that you may use it even before adding threading to your class.  
* If MyClass is threadsafe, then annotating with @singleton will give a threadsafe singleton (only the safety of creating the first instance requires locking, as all other singleton actions are no-ops or simply return a reference to the single instance)  
* If MyClass has locking (either Lock or RLock) in the initialization (new and init) the singleton locking does not deadlock.  
* The test suite is included in the src package, so you can tell if I verified correctly  
* The singleton decorator and test bench pass black and mypy  
* The test suite is run before publishing  

This has some fixes (correct calling of old init, correct replacement of init, removal of copy and deepcopy, and threadsafety) from the version on the PythonDecoratorLibrary wiki page.

```py
from singleton_decorator1 import singleton

@singleton
class MyClass
    pass

a = MyClass()
b = MyClass()
assert(a is b)
c = deepcopy(b)
assert(a is c)
```
Note that if MyClass is __not__ threadsafe, then the decorator will not fix 
that -- it only ensures that the singleton functionality is thread safe.

The library can be built with hatchling:  

[repository](https://codeberg.org/Sojournings/singleton-decorator.git)
[issues](https://codeberg.org/Sojournings/singleton-decorator/issues)
[PyPI](https://pypi.org/project/singleton-decorator1/)
