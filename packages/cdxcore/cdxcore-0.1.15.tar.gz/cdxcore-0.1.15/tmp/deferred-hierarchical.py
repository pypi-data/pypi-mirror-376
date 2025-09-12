"""
Overview
--------

Framework for delayed execution of a Python code tree.

Used by :mod:`cdxcore.dnaplot`.

Import
------

.. code-block:: python

    from cdxcore.deferrred import Deferred

"""

from .err import verify
from. util import qualified_name, fmt_list
from .verbose import Context
from collections.abc import Collection, Sequence, Mapping
import gc as gc

class ResolutionDependencyError(RuntimeError):
    """
    Exeception if the resolution of a deferred action failed because one
    of its source items has not been resolved.
    """
    pass        

class DeferredAction(object):
    """
    A deferred action keeps track of an action dependency tree
    for an object which has not been created, yet.
    
    This class is returned by :func:`cdxcore.deferred.Deferred`.
    
    The aim is to be able to record a sequence of actions on a placeholder
    for an object which does not yet exist
    such as function calls, item access, or attribute access,
    and store the resulting logical dependency tree. Once the target
    element is available, execute the dependency tree iteratively.

    A basic example is as follows: assume we have a class ``A`` of which
    we will create an object ``a``, but only at a later stage. We
    wish to record a list of deferred actions on ``a`` ahead of its creation.

    Define the class::
        
        class A(object):
            def __init__(self, x):
                self.x = x
            def a_func(self, y):
                return self.x * y
            @staticmethod
            def a_static(y):
                return y
            @property
            def a_propery(self):
                return self.x
            def __getitem__(self, y):
                return self.x * y
            def __call__(self, y):
                return self.x * y
            def another(self):#
                return A(x=self.x*2)

    Use :func:`cdxcore.deferred.Deferred` to create a root ``DeferredAction`` object::
        
        from cdxcore.deferred import Deferred
        da = Deferred("A")
        
    Record a few actions::

        af = da.a_func(1)    # defer function call to a_func(1)
        ai = da[2]           # defer item access
        aa = da.x            # defer attribute access

    :class:`cdxcore.deferred.DeferredAction` works iteratively, e.g. all values returned from a function call, ``__call__``, or ``__getitem__``
    are themselves deferred automatically.`:class:`cdxcore.deferred.DeferredAction` is also able to defer item and attribute assignments.
    
    As an example::

        an = da.another()
        an = an.another()     # call a.another().another() --> an.x = 1*2*2 = 4
        
    Finally, resolve the execution by instantiating ``A`` and calling :meth:`cdxcore.deferred.DeferredAction.deferred_resolve`::

        a = A()
        da.deferred_resolve( a )
        
        print( an.x )         # -> 4

    This functionality is used in :mod:`cdxcore.dynaplot`::

        from cdxcore.dynaplot import figure

        fig = figure()                # the DynanicFig returned by figure() is derived from DeferredAction
        ax  = fig.add_subplot()       # Deferred call for add_subplot()
        lns = ax.plot( x, y )[0]      # This is a deferred call to plot() and then [0].
        fig.render()                  # renders the figure and executes plot() then [0]
        lns.set_ydata( y2 )           # we can now access the resulting Line2D object via the DeferredAction wrapper
        fig.close()                   # update graph
    
    **Constructor**
    
    External applications do not usually need to directly create objects
    of type :class:`cdxcore.deferred.DeferredAction`. Use :func:`cdxcore.deferred.Deferred`
    as top level entry point.
    """

    def __init__(self, *, action      : str,       #: :meta private:
                          info        : str,       #: :meta private:
                          parent_info : str,       #: :meta private:
                          sources     : dict,      #: :meta private:
                          args        : Collection,#: :meta private: 
                          kwargs      : Mapping,   #: :meta private:
                          max_err_len : int,       #: :meta private:
                          ):
        """
        Initialize a deferred action.
        :meta private:
        """
        self.__max_err_len  = max_err_len
        
        verify( isinstance(info, str), lambda : f"'info' must be a string; found {self.__to_str(info)}.", exception=ValueError)
        verify( isinstance(parent_info, str), lambda : f"'parent_info' must be a string; found {self.__to_str(parent_info)}.", exception=ValueError)
        verify( isinstance(action, str), lambda : f"'action' must be a string; found {self.__to_str(action)}.", exception=ValueError)
        verify( isinstance(args, (Sequence,Collection)), lambda : f"'args' must be a Collection; found {type(args)}.", exception=ValueError)
        verify( isinstance(kwargs, Mapping), lambda : f"'kwargs' must be a Mapping; found {type(kwargs)}.", exception=ValueError)
        
        if action == "":
            verify( len(info)>0 and
                    len(parent_info) == 0 and
                    len(args) == 0 and
                    len(sources) == 0 and
                    len(kwargs) == 0, "Must specify 'info' but cannot specify 'parent_info', args', or 'kwargs' for the root action \"\"", exception=ValueError)
        
        self.__action       = action              # action code
        self.__parent_info  = parent_info
        self.__args         = args
        self.__kwargs       = kwargs
        self.__live         = None           # once the object exists, it goes here.
        self.__was_resolved = False          # whether the action was executed.
        self.__dependants   = []             # list of all dependent actions.
        
        if action == "":
            info            = "$"+info
            self.__sources  = {id(self):info}
            self.__info     = info
        else:
            self.__sources  = sources
            self.__info     = info
        
        self.__dict__["_ready_for_the_deferred_magic_"] = 1

    def __to_str( self, x ):
        """ Limit string 'x' to ``max_err_len`` by adding ``...`` if necessary. """
        x = str(x)
        if len(x) > self.__max_err_len:
            if x[-1] in [')', ']', '}']:
                x = x[:self.__max_err_len-4] + "..." + x[-1]
            else:
                x = x[:self.__max_err_len-3] + "..." 
        return x
    
    def __to_argstr( self, x ):
        if isinstance(x, DeferredAction):
            if not x.deferred_was_resolved:
                return f"{{{x.__info}}}"    
            x = x._live
        return str(x)

    def __fmt_args(self, args, kwargs ):
        args_   = [ self.__to_argstr(x) for x in args ]
        kwargs_ = { k: self.__to_argstr(x) for k,x in kwargs.items() }
        fmt_args = ""
        for _ in args_:
            fmt_args += str(_) + ","
        for _ in kwargs_.items():
            fmt_args += f"{_[0]}={_[1]},"
        return fmt_args[:-1]

    def __qualname( self, x ):
        """ Attempt to obtain a human readable name for ``x``/ """
        if x is None:
            return "None"
        name = getattr(x,"__qualname__", getattr(x, "__name__", None) )
        if not name is None:
            return name       
        try:
            return qualified_name( type(x) )
        except:
            pass                       
        return self.__to_str(x)

    @property
    def deferred_info(self) -> str:
        """
        Text description of the current action.
        
        Top level sources are indicated by a ``$``. Curly brackets ``{}`` indicate
        deferred actions themselves. For example:
        
        .. code-block:: python
        
            $a.f({$b.g(1)})
            
        Is generated by:
        
        .. code-block:: python

            from cdxcore.deferred import Deferred

            a = Deferred("a")
            b = Deferred("b")
            _ = a.f( b.g(1) )
            print( _.deferred_info )  # -> '$a.f({$b.g(1)})'
        """
        return self.__info
        
    @property
    def deferred_was_resolved(self) -> bool:
        """ Whether the underlying operation has already been resolved. """
        return self.__was_resolved
        
    @property
    def deferred_dependants(self) -> list:
        """ Retrieve list of dependant :class:`cdxcore.deferred.DeferredAction` objects. """
        return self.__dependants
        
    @property
    def deferred_sources(self) -> dict:
        """
        Retrieve a dictionary with information on all top-level sources
        this deferred action depends on.
        
        A top level source is an element which must be created explicitly by the user.
        These are the elements generated by :func:'cdxcore.deferred.Deferred'.

        The list contains a unique ``id`` and the name of the
        source. The ``id`` is used to allow the same name for
        several :func:`Deferred` elements.
        
        Most users will prefer a simple list of names of sources.
        In that case, use :meth:`cdxcore.deferred.Deferred.deferred_sources_names`.

        """
        return self.__sources
    
    @property
    def deferred_sources_names(self) -> list:
        """
        Retrieve a list of names of all top-level sources
        this deferred action depends on.
        
        A top level source is an element which must be created explicitly by the user.
        These are the elements generated by :func:'cdxcore.deferred.Deferred'.

        The list returned by this function contains the ``info`` names
        for each of the sources. 

        Example:
        
        .. code-block:: python

            from cdxcore.deferred import Deferred

            a = Deferred("a")
            b = Deferred("b")
            _ = a.f( b.g(1) )
            print( _.deferred_sources_names )  # -> ['$a', '$b']
            
        The purpose of this function is to allow users to detect dependencies on
        source objects and organize resolution code accordingly.
        """
        return list( self.deferred_sources.values() )
    
    @property
    def deferred_action_result(self):
        """
        Returns the result of the deferred action, if available.
        
        Raises a :class:`RuntimeError` if the action has not been
        executed with :meth:`cdxcore.deferred.Deferred.deferred_resolve` yet.        
        
        Note that this function might return ``None`` if the resolved
        action had returned ``None``.
        """
        verify( self.__was_resolved, lambda : f"Deferred action '{self.__info}' has not been executed yet" )
        return self.__live
    
    def deferred_print_dependency_tree( self, verbose : Context = Context.all, *, with_sources : bool = False ):
        """ 
        Prints the dependency tree recorded by this object and its descendants.
        
        This function must be called *before* :meth:`cdxcore.deferred.Deferred.deferred_resolve` is called
        (``deferred_resolve`` clears the dependency tree to free memory).
        
        You can collect this information manually as follows if required:

        .. code-block:: python

            from cdxcore.deferred import Deferred

            a = Deferred("a")
            b = Deferred("b")
            _ = a.f( b.g(1) )
            
            def collect(x,i=0,data=None):
                data = data if not data is None else list()
                data.append((i,x.deferred_info,x.deferred_sources_names))
                for d in x.deferred_dependants:
                    collect(d,i+1,data)
                return data
            for i, info, sources in collect(a):
                print( f"{' '*i} {info} <- {sources}" )    
                
        prints:
            
        .. code-block:: python

             $a <- ['$a']
              $a.f <- ['$a']
               $a.f({$b.g(1)}) <- ['$a', '$b']            
        """
        if with_sources:
            sources = sorted( self.__sources.values() )
            s = ""
            for _ in sources:
                s += _+","
            s = s[:-1]
            verbose.write( f"{self.__info} <= {s}" )
        else:
            verbose.write( self.__info )
                      
        for d in self.__dependants:
            d.deferred_print_dependency_tree( with_sources=with_sources, verbose=verbose(1) )

    def deferred_resolve(self, owner, verbose : Context = None ):
        """
        Executes the deferred action with ``owner`` as the subject of the action to be performed.
        
        For example, if the action is ``__getitem__`` parameter ``key``, then this function
        will execute ``owner[key]``, resolve all dependent functions, and then return the
        value of ``owner[key]``.
        """
        verbose = Context.quiet if verbose is None else verbose
        
        # deferred_resolve the deferred action
        verify( not self.__was_resolved, lambda : f"Deferred action '{self.__info}' has already been executed '{qualified_name(owner)}'" )
        verify( not owner is None, lambda : f"Cannot resolve '{self.__info}': the parent action '{self.__parent_info}' returned 'None'" )
        verify( not isinstance(owner, DeferredAction), lambda : f"Cannot resolve '{self.__info}' using a 'DeferredAction'" )
            
        if self.__action == "":
            # no action means `self` references the object itself
            live = owner
        
        else:
            def morph(x):
                if not isinstance(x, DeferredAction):
                    return x
                if x.deferred_was_resolved:
                    return x.__live
                raise ResolutionDependencyError(
                        f"Cannot resolve '{self.__info}' with the concrete element of type '{qualified_name(owner)}': "+\
                        f"execution is dependent on yet-unresolved element '{x.__info}'. "+\
                        "Resolve that element first. "+\
                        f"Note: '{self.__info}' is dependent on the following sources: {fmt_list(self.__sources.values(),sort=True)}."    
                        )  
            args   = [ morph(x) for x in self.__args ]        
            kwargs = { k: morph(x) for k,x in self.__kwargs.items() } 
            
            if self.__action == "__getattr__":
                # __getattr__ is not a standard member and cannot be obtained with getattr()
                try:
                    live = getattr(owner,*args,**kwargs)
                except AttributeError as e:
                    arguments = self.__fmt_args(args,kwargs)
                    parent = f"provided by '{self.__parent_info}' " if self.__parent_info!="" else ''
                    emsg   = f"Cannot resolve '{self.__info}': the concrete element of type '{qualified_name(owner)}' {parent}"+\
                             f"does not have the requested attribute '{arguments}'."
                    e.args = (emsg,) + e.args
                    raise e
            else:
                # all other properties -> standard handling
                try:
                    action = getattr(owner, self.__action)
                except AttributeError as e:
                    parent = f"provided by '{self.__parent_info}' " if self.__parent_info!="" else ''
                    emsg   = f"Cannot resolve '{self.__info}': the concrete element of type '{qualified_name(owner)}' {parent}"+\
                             f"does not contain the action '{self.__action}'"
                    e.args = (emsg,) + e.args
                    raise e
                
                try:
                            
                    live  = action( *args, **kwargs )
                except Exception as e:
                    arguments = self.__fmt_args(args,kwargs)
                    parent    = f"provided by '{self.__parent_info}' " if self.__parent_info!="" else ''
                    emsg = f"Cannot resolve '{self.__info}': when attempting to execute the action '{self.__action}' "+\
                           f"using the concrete element of type '{qualified_name(owner)}' {parent}"+\
                           f"with parameters '{arguments}' "+\
                           f"an exception was raised: {e}"
                    e.args = (emsg,) + e.args
                    raise e
                del action
       
        verbose.write(f"{self.__info} -> '{qualified_name(live)}' : {self.__to_str(live)}")
        # clear object
        # note that as soon as we write to self.__live we can no longer
        # access any information via getattr()/setattr()/delattr()

        # resolve all deferred calls for this object
        # note that self.__live might be None.
        while len(self.__dependants) > 0:
            self.__dependants.pop(0).deferred_resolve( live, verbose=verbose(1) )

        # make sure the parameter scope can be released
        # 'args' and 'kwargs' may hold substantial amounts of memory,
        # for example when this framework is used for delayed
        # plotting with cdxcore.dynaplot
        del self.__kwargs
        del self.__args
        gc.collect()
        
        # action
        self.__was_resolved = True
        self.__live = live
        
    # Iteration
    # =========
    # The following are deferred function calls on the object subject of the action ``self``.
    
    def _act( self, action     : str, *,
                    args       : Collection = [],
                    kwargs     : Mapping = {},
                    num_args   : int = None,
                    fmt        : str = None
                    ):
        """ Standard action handling """

        # we already have a live object --> action directly
        if self.__was_resolved:
            if action == "":
                return self._live
            if action == "__getattr__":
                return getattr(self._live, *args, **kwargs)
            try:
                element = getattr(self.__live, action)
            except AttributeError as e:
                emsg = f"Cannot route '{self.__info}' to the object '{qualified_name(self.__live)}' "+\
                       f"provided by '{self.__parent_info}': the object "+\
                       f"does not contain the action '{action}'"
                e.args = (emsg,) + e.args
                raise e
            
            return element(*args, **kwargs)
        
        # format info string
        fmt_args = lambda : self.__fmt_args(args,kwargs)
        if fmt is None:
            verify( num_args is None, f"Error defining action '{action}' for '{self.__info}': cannot specify 'num_args' if 'fmt' is None")
            info = f"{self.__info}.{action}({fmt_args()})"
        else:
            if not num_args is None:
                # specific list of arguments
                verify( num_args is None or len(args) == num_args, lambda : f"Error defining action '{action}' for '{self.__info}': expected {num_args} but found {len(args)}" )
                verify( len(kwargs) == 0, lambda : f"Error defining action '{action}' for '{self.__info}': expected {num_args} ... in this case no kwargs are expected, but {len(kwargs)} where found" )
                verify( not fmt is None, lambda : f"Error defining action '{action}' for '{self.__info}': 'fmt' not specified" )
    
                def label(x):
                    return x if not isinstance(x, DeferredAction) else x.__info
                arguments           = { f"arg{i}" : label(arg) for i, arg in enumerate(args) }
                arguments['parent'] = self.__info
                try:
                    info                = fmt.format(**arguments)
                except ValueError as e:
                    raise ValueError( fmt, e, arguments ) from e

            else:
                # __call__
                info = fmt.format(parent=self.__info, args=fmt_args())
        
        # detected dependencies in arguments on other
        sources = dict(self.__sources)
        for x in args:
            if isinstance(x, DeferredAction):
                sources |= x.__sources
        for x in kwargs.values():
            if isinstance(x, DeferredAction):
                sources |= x.__sources
        
        # create new action
        deferred  = DeferredAction( 
                              action=action,
                              parent_info=self.__info,
                              info=self.__to_str(info),
                              args=list(args),
                              kwargs=dict(kwargs),
                              max_err_len=self.__max_err_len,
                              sources=sources )
        self.__dependants.append( deferred )
        return deferred

    # Routed actions
    # --------------
    # We handle __getattr__ and __setattr__ explicitly


    def __getattr__(self, attr ):
        """ Deferred attribute access """
        #print("__getattr__", attr, self.__dict__.get(private_str+"info", "?"))
        private_str = "_DeferredAction__"    
        if attr in self.__dict__ or\
                   attr[:2] == "__" or\
                   attr[:len(private_str)] == private_str or\
                   not "_ready_for_the_deferred_magic_" in self.__dict__:
            #print("__getattr__: direct", attr)
            try:
                return self.__dict__[attr]
            except KeyError as e:
                raise AttributeError(*e.args, self.__dict__[private_str+"info"]) from e
        if not self.__live is None:
            #print("__getattr__: live", attr)
            return getattr(self.__live, attr)
        #print("__getattr__: act", attr)
        return self._act("__getattr__", args=[attr], num_args=1, fmt="{parent}.{arg0}")
    
    def __setattr__(self, attr, value):
        """ Deferred attribute access """
        #print("__getattr__", attr, self.__dict__.get(private_str+"info", "?"))
        private_str = "_DeferredAction__"    
        if attr in self.__dict__ or\
                   attr[:2] == "__" or\
                   attr[:len(private_str)] == private_str or\
                   not "_ready_for_the_deferred_magic_" in self.__dict__:
            try:
                self.__dict__[attr] = value
            except KeyError as e:
                raise AttributeError(*e.args, self.__dict__[private_str+"info"]) from e
            #print("__setattr__: direct", attr)
            return
        if not self.__live is None:
            #print("__setattr__: live", attr)
            return setattr(self.__live, attr, value)
        #print("__setattr__: act", attr)
        return self._act("__setattr__", args=[attr, value], num_args=2, fmt="{parent}.{arg0}={arg1}")

    def __delattr__(self, attr):
        """ Deferred attribute access """
        #print("__delattr__", attr)
        private_str = "_DeferredAction__"    
        if attr in self.__dict__ or\
                   attr[:2] == "__" or\
                   attr[:len(private_str)] == private_str or\
                   not "_ready_for_the_deferred_magic_" in self.__dict__:
            #print("__delattr__: direct", attr)
            try:
                del self.__dict__[attr]
            except KeyError as e:
                raise AttributeError(*e.args, self.__dict__[private_str+"info"]) from e
            return
        if not self.__live is None:
            #print("__delattr__: live", attr)
            return delattr(self.__live, attr)
        #print("__delattr__: act", attr)
        return self._act("__delattr__", args=[attr], num_args=1, fmt="del {parent}.{arg0}")

    @staticmethod
    def _generate_handle( action : str,
                          return_deferred : bool = True, *,
                          num_args : int = None,
                          fmt : str = None ):
        def act(self, *args, **kwargs):
            r = self._act(action, args=args, kwargs=kwargs, num_args=num_args, fmt=fmt )
            return r if return_deferred else self
        act.__name__ = action
        act.__doc__  = f"Deferred ``{action}`` action"
        return act
    
    # core functionality
    __call__    = _generate_handle("__call__", num_args=None, fmt="{parent}({args})")
    __setitem__ = _generate_handle("__setitem__", num_args=2, fmt="{parent}[{arg0}]={arg1}")
    __getitem__ = _generate_handle("__getitem__", num_args=1, fmt="{parent}[{arg0}]")

    # collections
    __contains__ = _generate_handle("__contains__", num_args=1, fmt="({arg0} in {parent})")
    __iter__     = _generate_handle("__iter__")
    __len__      = _generate_handle("__len__", num_args=0, fmt="len({parent})")
    __hash__     = _generate_handle("__hash__", num_args=0, fmt="hash({parent})")

    # cannot implement __bool__, __str__, or, __repr__ as these
    # have defined return types

    # comparison operators
    __neq__     = _generate_handle("__neq__", num_args=1, fmt="({parent}!={arg0})")
    __eq__      = _generate_handle("__eq__", num_args=1, fmt="({parent}=={arg0})")
    __ge__      = _generate_handle("__ge__", num_args=1, fmt="({parent}>={arg0})")
    __le__      = _generate_handle("__le__", num_args=1, fmt="({parent}<={arg0})")
    __gt__      = _generate_handle("__gt__", num_args=1, fmt="({parent}>{arg0})")
    __lt__      = _generate_handle("__lt__", num_args=1, fmt="({parent}<{arg0})")
    
    # i*
    __ior__      = _generate_handle("__ior__", False, num_args=1, fmt="{parent}|={arg0}")
    __iand__     = _generate_handle("__iand__", False, num_args=1, fmt="{parent}&={arg0}")
    __ixor__     = _generate_handle("__iand__", False, num_args=1, fmt="{parent}^={arg0}")
    __imod__     = _generate_handle("__imod__", False, num_args=1, fmt="{parent}%={arg0}")
    __iadd__     = _generate_handle("__iadd__", False, num_args=1, fmt="{parent}+={arg0}")
    __iconcat__  = _generate_handle("__iconcat__", False, num_args=1, fmt="{parent}+={arg0}")
    __isub__     = _generate_handle("__isub__", False, num_args=1, fmt="{parent}-={arg0}")
    __imul__     = _generate_handle("__imul__", False, num_args=1, fmt="{parent}*={arg0}")
    __imatmul__  = _generate_handle("__imatmul__", False, num_args=1, fmt="{parent}@={arg0}")
    __ipow__     = _generate_handle("__ipow__", False, num_args=1, fmt="{parent}**={arg0}")
    __itruediv__ = _generate_handle("__itruediv__", False, num_args=1, fmt="{parent}/={arg0}")
    __ifloordiv__ = _generate_handle("__ifloordiv__", False, num_args=1, fmt="{parent}//={arg0}")
    # Py2 __idiv__     = _generate_handle("__idiv__", False, num_args=1, fmt="{parent}/={arg0}")
    
    # binary
    __or__       = _generate_handle("__or__", num_args=1, fmt="({parent}|{arg0})")
    __and__      = _generate_handle("__and__", num_args=1, fmt="({parent}&{arg0})")
    __xor__      = _generate_handle("__xor__", num_args=1, fmt="({parent}^{arg0})")
    __mod__      = _generate_handle("__mod__", num_args=1, fmt="({parent}%{arg0})")
    __add__      = _generate_handle("__add__", num_args=1, fmt="({parent}+{arg0})")
    __concat__   = _generate_handle("__concat__", num_args=1, fmt="({parent}+{arg0})")
    __sub__      = _generate_handle("__sub__", num_args=1, fmt="({parent}-{arg0})")
    __mul__      = _generate_handle("__mul__", num_args=1, fmt="({parent}*{arg0})")
    __pow__      = _generate_handle("__pow__", num_args=1, fmt="({parent}**{arg0})")
    __matmul__   = _generate_handle("__matmul__", num_args=1, fmt="({parent}@{arg0})")
    __truediv__  = _generate_handle("__truediv__", num_args=1, fmt="({parent}/{arg0})")
    __floordiv__ = _generate_handle("__floordiv__", num_args=1, fmt="({parent}//{arg0})")
    # Py2__div__      = _generate_handle("__div__", num_args=1, fmt="({parent}/{arg0})")

    # rbinary
    __ror__       = _generate_handle("__ror__", num_args=1,      fmt="({arg0}|{parent})")
    __rand__      = _generate_handle("__rand__", num_args=1,     fmt="({arg0}&{parent})")
    __rxor__      = _generate_handle("__rxor__", num_args=1,     fmt="({arg0}^{parent})")
    __rmod__      = _generate_handle("__rmod__", num_args=1,     fmt="({arg0}%{parent})")
    __radd__      = _generate_handle("__radd__", num_args=1,     fmt="({arg0}+{parent})")
    __rconcat__   = _generate_handle("__rconcat__", num_args=1,  fmt="({arg0}+{parent})")
    __rsub__      = _generate_handle("__rsub__", num_args=1,     fmt="({arg0}-{parent})")
    __rmul__      = _generate_handle("__rmul__", num_args=1,     fmt="({arg0}*{parent})")
    __rpow__      = _generate_handle("__rpow__", num_args=1,     fmt="({arg0}**{parent})")
    __rmatmul__   = _generate_handle("__rmatmul__", num_args=1,  fmt="({arg0}@{parent})")
    __rtruediv__  = _generate_handle("__rtruediv__", num_args=1, fmt="({arg0}/{parent})")
    __rfloordiv__ = _generate_handle("__rfloordiv__", num_args=1,fmt="({arg0}//{parent})")
    # Py2__rdiv__      = _generate_handle("__rdiv__", num_args=1,     fmt="({arg0}/{parent})")
    
def Deferred( info : str,
              max_err_len  : int = 100
              ):
    """
    Create a :class:`cdxcore.deferred.DeferredAction` object to keep track
    of a dependency tree of a sequence of actions performed an object
    that does not yet exist.
    
    See :class:`cdxcore.deferred.DeferredAction` for a comprehensive discussion.

    Parameters
    ----------
    info : str
        Descriptive name of the usually not-yet-created object deferred actions
        will act upon.
        
    max_err_len : int, optional
        Maximum length of output information. The default is 100.

    Returns
    -------
    :class:`cdxcore.deferred.DeferredAction`
        A deferred action.
    """
    return DeferredAction( info=info,
                           action="", 
                           parent_info="", 
                           sources={},
                           args=[], 
                           kwargs={},
                           max_err_len=max_err_len )
    
    