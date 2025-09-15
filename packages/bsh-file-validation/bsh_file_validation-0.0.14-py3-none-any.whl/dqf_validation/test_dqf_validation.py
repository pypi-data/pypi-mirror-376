from my_package import enryption_dqf_validation

dqf_validate = dqf_validation.DQFValidation(
    SourceSystem="TestData",
    HierarchyFlag=False,
    IOTFlag=False,
    FNT_ID="327",
    FileTemplate="T_Employee_Data_csv"
)
dqf_validate.validate()