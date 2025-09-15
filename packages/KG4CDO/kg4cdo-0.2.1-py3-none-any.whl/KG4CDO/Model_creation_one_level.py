
def create_model():
    num_users = 7500000
    num_ppv = 7500000


    # Open csv file
    model_csv = open("TMP/Test_model.csv", "wt")
    facts1_csv = open("TMP/Test_facts1.csv", "wt")
    facts2_csv = open("TMP/Test_facts2.csv", "wt")
    header_mod = 'MODEL_TYPE,NODE_TYPE,ID,NAME,PARENT_ID,LEVEL_NUM\n'
    header_fact = 'MODEL_TYPE,NODE_TYPE,FACT_ID,NAME,PARENT_ID,LEVEL_NUM\n'
    #Open and read template
    template = open("Test_template_1-one-level.csv", "r")
    body = template.read()
    # Add header and template
    model_csv.write(header_mod)
    facts1_csv.write(header_fact)
    facts2_csv.write(header_fact)
    model_csv.write(body)
    facts1_csv.write(body)
    facts2_csv.write(body)

    template.close()

    # Create PPV events nodes
    for i in range(num_ppv):
        body = "PPV,PPV_Event," + str(i) + ",Event_" + str(i) + ",,0\n"
        model_csv.write(body)
        facts1_csv.write(body)
        facts2_csv.write(body)

    # Create Device user nodes
    for i in range(num_users):
        body = "User,User," + str(i) + ",User_" + str(i) + ",,0\n"
        model_csv.write(body)
        facts1_csv.write(body)
        facts2_csv.write(body)

    #Close file
    model_csv.close()
    facts1_csv.close()
    facts2_csv.close()

    return 1

if __name__ == "__main__":
    create_model()