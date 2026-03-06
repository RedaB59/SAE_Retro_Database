
CREATE TABLE IF NOT EXISTS departements (
    code_dep VARCHAR(2) PRIMARY KEY,
    lib_dep VARCHAR(255)
);


CREATE TABLE IF NOT EXISTS communes (
	code_com VARCHAR(5) PRIMARY KEY,
	code_postal VARCHAR(5),
	lib_com VARCHAR(255),
	ancien_code_commune VARCHAR(5),
	ancien_libelle_commune VARCHAR(255),
	code_dep VARCHAR(2) references departements (code_dep)
);



CREATE TABLE IF NOT EXISTS natures_culture_speciales (
    id_nat_cult_spe VARCHAR(5) PRIMARY KEY,
	lib_nat_cult_spe VARCHAR(255)
);


CREATE TABLE IF NOT EXISTS natures_culture (
	id_nat_cult VARCHAR(2) PRIMARY key,
	lib_nat_cult VARCHAR(255)
);



CREATE TABLE IF NOT EXISTS nature_mutation (
	id_nat_mut SMALLINT PRIMARY KEY,
	lib_nat_mut VARCHAR(255) NOT NULL
);


CREATE TABLE IF NOT EXISTS types_local (
    id_type_loc SMALLINT PRIMARY key,
    lib_type_loc varchar(255) NOT NULL
);   