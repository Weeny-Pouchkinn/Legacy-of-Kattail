def rgb_to_normalized_script():
    try:
        raw_input_values = input("Enter RGB values (e.g., 191 189 123): ")
        r, g, b = map(int, raw_input_values.strip().split())

        if not all(0 <= val <= 255 for val in (r, g, b)):
            raise ValueError("All values must be between 0 and 255.")

        r_norm = round(r / 255, 3)
        g_norm = round(g / 255, 3)
        b_norm = round(b / 255, 3)

        indent = "\t" * 5
        print(f"set_temp_variable = {{ red = {r_norm} }}")
        print(f"set_temp_variable = {{ green = {g_norm} }}")
        print(f"set_temp_variable = {{ blue = {b_norm} }}")

    except Exception as e:
        print("Error:", e)

    input("\nPress Enter to exit...")  # Keeps the terminal open

if __name__ == "__main__":
    rgb_to_normalized_script()
