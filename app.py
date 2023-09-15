import streamlit as st
import nufhe
import pycuda.autoinit
ctx = nufhe.Context()
secret_key, cloud_key = ctx.make_key_pair()
vm = ctx.make_virtual_machine(cloud_key) 
st.title("Calculator App using Streamlit")
 
# creates a horizontal line
st.write("---")
 
# input 1
num1 = st.number_input("Input Number1", min_value=1,max_value=65536,value=5,step=1,key=1)
 
# input 2
num2 = st.number_input("Input Number2", min_value=1,max_value=65536,value=5,step=1,key=2)
 
st.write("Operation")
 
operation = st.radio("Select an operation to perform:",
                    ("Add", "Subtract", "Multiply", "Divide"))
 
ans = 0
def add():
    size=16
    bits = [[False] for i in range(size - 2)]
    zeros = [[False] for i in range(size)]

    bits1 = [[True]] + [[False]] + bits
    #print(bits1)
    bits2 = [[True]] + [[True]] + bits
    deci_x = num1
    deci_y = num2
    x=[]
    x = fixSizeBoolList(deci_x,size)
    y = fixSizeBoolList(deci_y,size)
    ciphertext1 = [[vm.empty_ciphertext((1,))] for i in range(size)]
    ciphertext2 = [[vm.empty_ciphertext((1,))] for i in range(size)]
    for i in range(size):
        ciphertext1[i] = ctx.encrypt(secret_key, x[i])
        ciphertext2[i] = ctx.encrypt(secret_key, y[i])
    #ciphertext1 = ctx.encrypt(secret_key, x)
    #ciphertext2 = ctx.encrypt(secret_key, y) 
    ciphertext1.reverse()
    ciphertext2.reverse()
    #result = addNumbers(ciphertext1, ciphertext2, size)
    result = addNumbers(ciphertext1, ciphertext2, secret_key, size, size)
    result.reverse()
    result_bits = [ctx.decrypt(secret_key, result[i]) for i in range(size)]
    return boolListToInt(result_bits) 
def calculate():
    if operation == "Add":
        ans = add(num1, num2)
    elif operation == "Subtract":
        ans = num1 - num2
    elif operation == "Multiply":
        ans = num1 * num2
    elif operation=="Divide" and num2!=0:
        ans = num1 / num2
    else:
        st.warning("Division by 0 error. Please enter a non-zero number.")
        ans = "Not defined"
 
    st.success(f"Answer = {ans}")
 
if st.button("Calculate result"):
    calculate()
def fixSizeBoolList(decimal,size):
    x = [int(x) for x in bin(decimal)[2:]]
    x = list(map(bool, x))
    x = [False]*(size - len(x)) + x
    pow2 = []
    for i in range(size):
      pow2.append([x[i]])
    return pow2
def boolListToInt(bitlists):
    out = 0
    for bit in bitlists:
        out = (out << 1) | bit
    return out

def addBits(r, a, b, carry):
    # Xor(t1[0], a, carry[0])
    t1 = vm.gate_xor(a, b)
    # Xor(t2[0], b, carry[0])
    

    # Xor(r[0], a, t2[0])
    r[0] = vm.gate_xor(t1, carry)
    # And(t1[0], t1[0], t2[0])
    t2 = vm.gate_and(a, carry)
    t3 = vm.gate_and(b, carry)
    t4=vm.gate_and(a,b)
    t5= vm.gate_or(t2,t3)
    # Xor(r[1], carry[0], t1[0])
    r[1] = vm.gate_or(t5, t4)

    return r


def addNumbers(ctA, ctB, nBits):
    ctRes = [[vm.empty_ciphertext((1,))] for i in range(nBits)]
    # carry = vm.empty_ciphertext((1,))
    bitResult = [[vm.empty_ciphertext((1,))] for i in range(2)]
    ctRes[0] = vm.gate_xor(ctA[0], ctB[0])
    # Xor(ctRes[0], ctA[0], ctB[0])
    carry = vm.gate_and(ctA[0], ctB[0])
    # And(carry[0], ctA[0], ctB[0])
    for i in range(1,nBits ):
        bitResult = addBits(bitResult, ctA[i], ctB[i], carry)
        # Copy(ctRes[i], bitResult[0]);
        ctRes[i] = nufhe.LweSampleArray.copy(bitResult[0])

        # Copy(carry[0], bitResult[1])
        carry = nufhe.LweSampleArray.copy(bitResult[1])

    return ctRes    