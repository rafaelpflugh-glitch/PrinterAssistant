from profiles.loader import ProfileLoader

loader = ProfileLoader()

profile = loader.detect("Lexmark MS610dn")

print(profile.info())
