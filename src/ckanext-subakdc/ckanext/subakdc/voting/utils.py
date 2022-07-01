def initdb():
    from ckanext.subakdc.voting import model

    model.init_tables()
