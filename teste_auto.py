from tools.auto_detect import detectar



resultado = detectar()



print()

print("==============================")
print("IMPRESSORAS ENCONTRADAS")
print("==============================")



for p in resultado:


    print()

    print(
        "IP:",
        p["ip"]
    )

    print(
        "EWS:",
        p["endpoint"]
    )