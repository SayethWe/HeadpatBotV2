import io, pickle


#courtesy https://stackoverflow.com/a/53327348
class RenameUnpickler(pickle.Unpickler):
    changedNames = {
        "Poll":"WaifuPoll"
    }
    changedModules = {

    }

    def find_class(self, module, name):
        renamed_module = module
        renamed_name = name
        if name in RenameUnpickler.changedNames:
            renamed_name = RenameUnpickler.changedNames[name]
        if module in RenameUnpickler.changedModules:
            renamed_name = RenameUnpickler.changedModules[module]

        return super(RenameUnpickler, self).find_class(renamed_module, renamed_name)


def load(file_obj):
    return RenameUnpickler(file_obj).load()


def loads(pickled_bytes):
    file_obj = io.BytesIO(pickled_bytes)
    return load(file_obj)

def dump(object,file,protocol=None,*args,**kwargs):
    return pickle.dump(object,file,protocol,*args,**kwargs)

def dumps(object,protocol=None,*args,**kwargs):
    return pickle.dumps(object,protocol,*args,**kwargs)
