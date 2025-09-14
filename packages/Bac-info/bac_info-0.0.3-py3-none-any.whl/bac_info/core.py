def saisir_n(bi, bs):
    """
    Prompt user to input an integer within a specified range.
    
    Args:
        bi (int): Lower bound (inclusive)
        bs (int): Upper bound (inclusive)
    
    Returns:
        int: Valid integer within the range [bi, bs]
    """
    n = int(input("Donner un entier : "))  # Get initial integer input
    # Keep asking until input is within valid range
    while not(bi <= n <= bs):
        print("Ce n'est pas un entier valide.")
        n = int(input("Donnez un entier valide : "))
    return n

def saisir_f(bi, bs):
    """
    Prompt user to input a float within a specified range.
    
    Args:
        bi (float): Lower bound (inclusive)
        bs (float): Upper bound (inclusive)
    
    Returns:
        float: Valid float within the range [bi, bs]
    """
    n = float(input("Donner un réel : "))  # Get initial float input
    # Keep asking until input is within valid range
    while not(bi <= n <= bs):
        print("Ce n'est pas un réel valide.")
        n = float(input("Donner un réel valide :"))  # BUG: Should be float(input())
    return n

def saisir_ch():
    """
    Prompt user to input a string containing only alphabetic characters.
    
    Returns:
        str: Valid alphabetic string (whitespace stripped)
    """
    ch = str(input("Donner une chaîne de caractères : ")).strip()  # Get input and remove whitespace
    # Keep asking until input contains only alphabetic characters
    while not (ch.isalpha()):
        print("Ce n'est pas une chaîne de caractères . Essayez encore.")
        ch = str(input("Donner une chaîne de caractères valide : "))  # Missing .strip() here
    return ch

def afficher_t(n, t):
    """
    Display array elements with their indices.
    
    Args:
        n (int): Number of elements to display
        t (list): Array/list to display
    """
    # Display each element with its index
    for i in range(n):
        print(f"t[{i}]=", t[i])

def afficher_m(m, n):
    """
    Display a square matrix with indices.
    
    Args:
        m (2D array): Matrix to display
        n (int): Size of the square matrix (n x n)
    """
    # Display matrix row by row
    for i in range(n):
        for j in range(n):
            print(f"m[{i,j}]=", m[i, j], end="")  # Print element on same line
        print()  # New line after each row

def remplir_m(m, n):
    """
    Fill a square matrix with integer values from user input.
    
    Args:
        m (2D array): Matrix to fill (modified in place)  
        n (int): Size of the square matrix (n x n)
    """
    for i in range(n):
        for j in range(n):
            m[i, j] =int(input(f"m[{i},{j}] = "))# NumPy-style indexing

def remplir_m_f(m, n):
    """
    Fill a square matrix with float values from user input.
    
    Args:
        m (2D array): Matrix to fill (modified in place)
        n (int): Size of the square matrix (n x n)
    """
    # Fill matrix element by element with floats
    for i in range(n):
        for j in range(n):
            m[i, j] =float(input(f"m[{i},{j}] = "))# NumPy-style indexing

def remplir_m_ch(m, n):
    """
    Fill a square matrix with string values from user input.
    
    Args:
        m (numpy.ndarray): Matrix to fill (modified in place)
        n (int): Size of the square matrix (n x n)
    """
    for i in range(n):
        for j in range(n):
            m[i, j] = input(f"m[{i},{j}] = ")  # NumPy-style indexing
def remplir_t(n, t):
    """
    Fill an array with integer values from user input.
    
    Args:
        n (int): Number of elements to fill
        t (list): Array to fill (modified in place)
    """
    # Fill array element by element
    for i in range(n):
        t[i] = int(input(f"t[{i}] = "))
def remplir_t_f(n, t):
    """
    Fill an array with float values from user input.
    
    Args:
        n (int): Number of elements to fill
        t (list): Array to fill (modified in place)
    """
    for i in range(n):
        t[i] = float(input(f"t[{i}] = "))

def remplir_t_ch(n, t):
    """
    Fill an array with string values from user input.
    
    Args:
        n (int): Number of elements to fill
        t (list): Array to fill (modified in place)
    """
    # Fill array element by element with strings
    for i in range(n):
        t[i] = str(input(f"t[{i}] = "))  # Prompt shows literal "i" instead of actual index

def existance_t(t, n, x):
    """
    Check if a value exists in an array.
    
    Args:
        t (list): Array to search in
        n (int): Number of elements to check
        x: Value to search for
    
    Returns:
        bool: True if value exists, False otherwise
    """
    test = False
    # Linear search through array
    for i in range(n):
        if t[i] == x:
            test = True  # Could use 'return True' here for early exit
    return test

def existance_ch(c, ch):
    """
    Check if a character exists in a string.
    
    Args:
        c (str): Character to search for
        ch (str): String to search in
    
    Returns:
        bool: True if character exists, False otherwise
    """
    test = False
    # Linear search through string
    for i in range(len(ch)):
        if ch[i] == c:
            test = True  # Could use 'return True' here for early exit
    return test

def existance_int(c, x):
    """
    Check if a digit exists in an integer.
    
    Args:
        c (int): Digit to search for
        x (int): Integer to search in
    
    Returns:
        bool: True if digit exists, False otherwise
    """
    ch = str(x)  # Convert integer to string for digit-by-digit search
    test = False
    # Search for digit in string representation
    for i in range(len(ch)):
        if ch[i] == str(c):
            test = True  # Could use 'return True' here for early exit
    return test

def pgcd(a, b):
    """
    Calculate the Greatest Common Divisor (PGCD) using Euclidean subtraction.
    
    Args:
        a (int): First integer
        b (int): Second integer
    
    Returns:
        int: Greatest Common Divisor of a and b
    """
    # Euclidean algorithm using subtraction
    a, b = abs(a), abs(b)
    if a == 0:
        return b
    if b == 0:
        return a
    while b != 0:
        a, b = b, a % b
    return a

def puissance(a, b):
    """
    Calculate a raised to the power of b using iterative multiplication.
    
    Args:
        a (int/float): Base number
        b (int): Exponent 
    """
    if b == 0:
        return 1  # Par convention, a^0 = 1
    if b < 0:
        if a == 0:
            raise ValueError("0 puissance un nombre négatif est indéfini.")
        return 1 / puissance(a, -b)

    result = 1
    for _ in range(b):
        result *= a
    return result

def sommechiffre(ch):
    """
    Calculate the sum of all digits in a string representation of a number.
    
    Args:
        ch (str): String containing digits
    
    Returns:
        int: Sum of all digits
    """
    s = 0  # Initialize sum
    # Add each digit to sum
    for i in range(len(ch)):
        s = s + int(ch[i])  # Convert character to int and add
    return s

def palindrom(ch):
    """
    Check if a string is a palindrome.
    
    Args:
        ch (str): String to check
    
    Returns:
        bool: True if string is a palindrome, False otherwise
    """
    test = True
    i = 0
    # Compare characters from start and end moving inward
    while(i < len(ch)/2 and test):
        if ch[i] != ch[len(ch)-i-1]:  # Compare symmetric positions
            test = False
        else:
            i = i + 1
    return test