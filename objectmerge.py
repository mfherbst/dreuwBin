# vi: set et ts=4 sw=4 sts=4:

class MergeException(Exception):
    """
    Exception thrown when merging two objects does
    not work (i.e. because both patches have respective
    values set.)
    """
    def __init__(self,message):
        super(MergeException, self).__init__(message)

class objectmerge:
    """
        Merges objects into the receiver object

        I.e. variables implementing the extend method are extended by the
        relevant values in the sender objects

        Variables that are none will be set to the values in the sender object

        if variable is already set, a MergeException will be thrown
    """

    def __init__(self,receiver):
        self.__receiver = receiver

    @property
    def receiver(self):
        return self.__receiver

    def merge_in(self,sender):
        """
        Merge this other object into the receiver

        Throws a MergeException if this is not possible

        Reasons for this are for example:
        The two objects contain deviating data on the same fields
        (which are not lists).
        """

        res = self.__assert_mergeable(sender)
        if res is not None:
            raise MergeException(res)

        sender_vars = vars(sender)
        rec_vars = vars(self.receiver)

        for var in rec_vars:
            if sender_vars[var] is None:
                continue

            if rec_vars[var] is None:
                rec_vars[var] = sender_vars[var]
                continue

            # see if rec_vars[var] has the extend method:
            extend_op = getattr(rec_vars[var], "extend", None)
            if callable(extend_op):
                extend_op(sender_vars[var])
                continue

    def __assert_mergeable(self,sender):
        """
        Test whether other is mergable into receiver. If this fails
        spit out the reason why, else return None
        """
        if not issubclass(type(sender), type(self.receiver)):
            return "Types of receiver and sender do not match"

        sender_vars = vars(sender)
        rec_vars = vars(self.receiver)

        for var in rec_vars:
            if rec_vars[var] is None or sender_vars[var] is None:
                continue

            if rec_vars[var] == sender_vars[var]:
                continue

            # see if rec_vars[var] has the extend method:
            extend_op = getattr(rec_vars[var], "extend", None)
            if callable(extend_op):
                continue

            # one criteria did not work
            return ("Could not merge variable " + str(var))
        return None

    def is_mergable(self,sender):
        """
        Return true if a merge is going to be successful
        """
        return (self.__assert_mergeable(sender) is None)

if __name__ == "__main__":
    class A:
        def __init__(self):
            self.nonvar=None
            self.listvar=["a"]
            self.tuplevar=tuple()

        def print(self):
            print(vars(self))

    class B(A):
        def __init__(self):
            super(B, self).__init__()
            self.fthvar = None


    a1 = A()
    a2 = A()
    a3 = B()

    a2.nonvar=42
    a2.listvar=["b"]
    a3.tuplevar=(1, 2)
    
    # here a2 is mergeable into a1
    # but a3 is not mergeable into a2
    # but a3 is mergable into a2

    merger1 = objectmerge(a1)
    merger2 = objectmerge(a2)

    # ---------------------
    # test merge a3 -> a1 (fails)
    if merger1.is_mergable(a3):
        a1.print()
        a3.print()
        raise SystemExit("Unit Test Error: a3 reported as mergable into a1")

    try:
        merger1.merge_in(a3)
        a1.print()
        a3.print()
        raise SystemExit("Unit Test Error: a3 could be merged into a1 without error")
    except MergeException:
        pass

    # ---------------------
    # test merge a3 -> a2 (fails)
    if merger2.is_mergable(a3):
        a2.print()
        a3.print()
        raise SystemExit("Unit Test Error: a3 reported as mergable into a2")

    try:
        merger2.merge_in(a3)
        a2.print()
        a3.print()
        raise SystemExit("Unit Test Error: a3 could be merged into a2 without error")
    except MergeException:
        pass

    # ---------------------
    # test merge a2 -> a1 (works)
    if not merger1.is_mergable(a2):
        a1.print()
        a2.print()
        raise SystemExit("Unit Test Error: a2 reported as unmergable into a1")

    try:
        merger1.merge_in(a2)
    except MergeException as e:
        a1.print()
        a2.print()
        raise e

    if (a1.nonvar != 42 or a1.listvar != [ "a","b" ]
            or a1.tuplevar != tuple() ):
        a1.print()
        raise SystemExit("Unit Test Error: a1 after merge not as expected")
    
    if (a2.nonvar != 42 or a2.listvar != [ "b" ]
            or a2.tuplevar != tuple() ):
        a2.print()
        raise SystemExit("Unit Test Error: a2 after merge not as expected")
   
    # alter a1
    a1.tuplevar=(1, 2)

    # ---------------------
    # test merge a2 -> a1 (works)
    if not merger1.is_mergable(a3):
        a1.print()
        a3.print()
        raise SystemExit("Unit Test Error: a3 reported as unmergable into modified a1")

    try:
        merger1.merge_in(a3)
    except MergeException as e:
        a1.print()
        a3.print()
        raise e

    if (a1.nonvar != 42 or a1.listvar != [ "a","b" ,"a"]
            or a1.tuplevar != (1,2) ):
        a1.print()
        raise SystemExit("Unit Test Error: a1 after second merge not as expected")

    #if (a3.nonvar != None or a3.listvar != [ "a" ]
    #        or a3.tuplevar != (1,2) ):
    #    a3.print()
    #    raise SystemExit("Unit Test Error: a3 after merge not as expected")


