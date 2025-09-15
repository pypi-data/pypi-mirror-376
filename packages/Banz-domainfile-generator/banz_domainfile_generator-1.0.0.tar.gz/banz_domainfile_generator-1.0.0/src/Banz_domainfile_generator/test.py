from domainfile_generator import run


csvTest = 'organization;Person;name,STRING,required;firstName,STRING;dateOfBirth,DATE;gender,ENUM(Gender/MALE/FEMALE/DIVERSE),required;memberships,INCOMING_REFERENCE(organization.Membership/n);contacts,INCOMING_REFERENCE(fan.Contact/n)'
csvTest += '\norganization;Contact;validFrom,DATE,required;validTo,DATE;type,ENUM(ContactType/EMAIL/ADDRESS/PHONE),required;street,STRING;number,STRING;numberSuffix,STRING;postbox,STRING;zip,STRING;city,STRING;country,STRING;email,STRING;countryCode,STRING;phoneNumber,STRING;person,REFERENCE(organization.Person),required'

paths = {
    'domain': '\\test\\backend\\domain\\src\\main\\java\\org\\derbanz\\cluborga\\domain\\',
    'schema': '\\test\\backend\\domain\\src\\main\\resources\\schema\\',
    'logic': '\\test\\backend\\logic\\src\\main\\java\\org\\derbanz\\cluborga\\logic\\',
    'commonService': '\\test\\backend\\service\\common\\src\\main\\java\\org\\derbanz\\cluborga\\commonservice\\',
    'uiService': '\\test\\backend\\service\\ui\\src\\main\\java\\org\\derbanz\\cluborga\\uiservice\\'
}
    

run(csvTest, paths)