from therm import Ingredient, Mixture


def main():
    Ingredient.readFile("data/PEPCODED.DAF")

    NC1260 = Ingredient.getLine(683)
    RDX = Ingredient.getLine(847)

    EC = Ingredient(
        name="Ethyl Centralite",
        elements={"C": 17, "H": 20, "O": 1, "N": 2},
        rho=1.140,
        rho_u="g/cc",
        Hf=-391.5,
        Hf_u="J/g",
    )

    ATEC = Ingredient(
        name="Acetyl triethyl citrate",
        elements={"C": 14, "H": 22, "O": 8},
        rho=1.136,
        rho_u="g/cc",
        # Hf=-1257,
        Hf=-5459.6,
        Hf_u="J/g",
    )

    CAB = Ingredient(
        "Cellulose Acetate Butyrate",
        elements={"C": 15, "H": 22, "O": 8},
        Hf=-4933.76,
        Hf_u="J/g",
        rho=1.220,
        rho_u="g/cc",
    )

    BDNPA = Ingredient.getLine(189)
    BDNPF = Ingredient.getLine(190)

    XM39 = Mixture(
        "XM39",
        compoDict={RDX: 76, CAB: 12, NC1260: 4, ATEC: 7.6, EC: 0.4},
    )

    XM39.prettyPrint()

    M43 = Mixture(
        name="M43",
        compoDict={
            RDX: 76,
            CAB: 12,
            NC1260: 4,
            BDNPA: 7.6,
            # BDNPF: 7.6,
            EC: 0.4,
        },
        Delta=0.2,
    )
    M43.prettyPrint()

    NG = Ingredient.getLine(693)

    MeNENA = Ingredient(
        "Methyl-NENA",
        elements={"C": 3, "H": 7, "N": 3, "O": 5},
        Hf=-106.50,  # Burcat, 2015
        Hf_u="kJ/mol",
        rho=1.53,  # a.la ADA377866
        rho_u="g/cc",
    )

    EtNENA = Ingredient(
        "Ethyl-NENA",
        elements={"C": 4, "H": 9, "N": 3, "O": 5},
        Hf=-133.90,  # Burcat, 2015
        Hf_u="kJ/mol",
        rho=1.32,  # a.la ADA377866
        rho_u="g/cc",
    )

    ATKPRD20 = Mixture(
        name="ATK PRD20",
        compoDict={
            NC1260: 41.90,
            RDX: 25.71,
            MeNENA: 14.00,
            EtNENA: 10.00,
            NG: 7.69,
        },
        Delta=0.2,
    )

    ATKPRD20.prettyPrint()

    ATKPRDS21 = Mixture(
        name="ATK PRD(S)21",
        compoDict={
            NC1260: 36.48,
            RDX: 30.33,
            MeNENA: 13.44,
            EtNENA: 9.57,
            NG: 9.46,
        },
        Delta=0.2,
    )

    ATKPRDS21.prettyPrint()

    ATKPRDS22 = Mixture(
        name="ATK PRD(S)22",
        compoDict={
            NC1260: 31.11,
            RDX: 34.08,
            MeNENA: 12.57,
            EtNENA: 8.94,
            NG: 12.58,
        },
        Delta=0.2,
    )

    ATKPRDS22.prettyPrint()


if __name__ == "__main__":
    main()
