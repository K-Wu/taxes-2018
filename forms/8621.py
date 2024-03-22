from . import utils


def fill_in_form(data_dict, identifier):
    utils.write_fillable_pdf("f8621.pdf", data_dict, "f8621.keys", identifier)
