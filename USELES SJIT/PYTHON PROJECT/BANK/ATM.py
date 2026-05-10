import os
import time

#=========/ ASK FOR USER ACCOUNT ID \==========
def user_id():
    global user_ID#SET VARIABLE TO BE GLOBAL

    user_ID = input("PLEASE ENTER YOUR ACCOUNT ID: ")#ASK FOR USER ACCOUNT ID

    #-----------| IF USER ENTER A SPACE OR NO CHARACTER |-----------
    while len(user_ID) == 0 or user_ID == " ":
        user_ID = input("INPUT AT LEAST A SINGLE CHARACTER \nPLEASE ENTER YOUR ACCOUNT ID: ")

    return user_ID

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#=========/ CHECK IF THAT ACCOUNT EXIST \==========
ACCOUNT_FILE = fr"C:\Users\CJ\Desktop\BANK\ACCOUNTS\{user_id()}.txt"
for _ in range(2):
    if os.path.exists(ACCOUNT_FILE):
        print("NOW LOOKING FOR YOUR ACCOUNT"),time.sleep(2)
        print(f"YOUR ACCOUNT HAS BEEN FOUND\nREGISTERED ACCOUNT : #{user_ID}"), time.sleep(0.5)
        print(time.strftime("DATE:%Y-%m-%d \nTIME:%H:%M:%S", time.localtime()))
        break

    else:
        print("NOW LOOKING FOR YOUR ACCOUNT"), time.sleep(2)
        print("YOUR ACCOUNT DOES NOT EXIST"), time.sleep(0.5)
        if _ == 1:#THIS END THE PROGRAM IF USER ENTERS TOO MUCH
            exit()

        ACCOUNT_FILE = fr"C:\Users\CJ\Desktop\BANK\ACCOUNTS\{user_id()}.txt"


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##=========/ CHECK PIN CORRECT \==========
file_op = open(ACCOUNT_FILE,"r")#Read and collect pin and account from file
pin,amount = file_op.read().split(",")#extracts pin and amount from inputted file

#=========/ CHECK FOR CORRECT OR INCORRECT INPUT \==========
for _ in range(2):#GIVE USER 2 TRY UNTIL CORRECT OR INCORRECT INPUT
    user_ID = input("PLEASE ENTER YOUR PIN: ")#ASK FOR PIN

    if user_ID == pin:
       print("NOW PROCESSING PIN..."),time.sleep(1.5)
       print("ACCESS GRANTED")
       break
    else:
        if _ == 1: print("TOO MANY TRY'S\nTRY AGAIN LATER"),exit()
        print("NOW PROCESSING PIN..."), time.sleep(1.8)
        print("WRONG PIN,PLEASE TRY AGAIN")



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#=========/ TRANSACTION \==========
T_transaction = input("HELLO WHAT ARE YOU DOING TODAY\nWITHDRAW [W] OR DEPOSIT [D] -> ").upper()  # ASK FOR TYPE OF TRANSACTION

while T_transaction not in ["W","D"]:
    T_transaction = input("INVALID INPUT\nEITHER PICK WITHDRAW [W] OR DEPOSIT [D] -> ").upper()


#========={ WITHDRAW }==========
if T_transaction == "W":#IF USER IS WITHDRAWING
    #amount = float(amount)  # change amount to an int

    if float(amount) <= 0:
        with open(ACCOUNT_FILE, "w") as FL:  # ADD 0 TO FILE IF
            FL.write(str(pin) + "," + str("0"))

        print("ACCOUNT AMOUNT IS EMPTY\nGOOD BYE"),exit()#IF ACCOUNT IS EMPTY
    print("PROCESSING REQUEST....\nPLEASE WAIT"),time.sleep(2)

    while True:
        try:
            A_withdrawn = float(input("HOW MUCH ARE WITHDRAWING TODAY?\nAMOUNT: "))
            break
        except ValueError:
            print("INVALID INPUT")
            continue
    print(f"DEDUCTED -> -${str(A_withdrawn)}") # show how much is withdrawing


#_____________________________________________________________________________________________

    ask_t = input("WOULD YOU LIKE TO HAVE ANOTHER WITHDRAWN\nYES[Y] OR NO[N]: ").upper()

    if ask_t == "Y":#IF USER PICK YES T ANOTHER WITHDRAW
        while True:
            try:
                A2_withdrawn = float(input("HOW MUCH ARE WITHDRAWING TODAY?\nAMOUNT: "))
                break
            except ValueError:
                print("INVALID INPUT")
                continue
        print(f"DEDUCTED -> -${str(A2_withdrawn)}")  # show how much is withdrawing

        total_withdraw = float(A_withdrawn) + float( A2_withdrawn)  # RETURN FIRST AND SECOND  WITHDRAWN IF USER PICK YES
        withdrawing = float(amount) - float(total_withdraw)#SHOW USER 2 TOTAL WITHDRAW
        print("TOTAL WITHDRAW -> -$", total_withdraw)#ALRITHMITIC OF THE WITHDRAWING

        #PRINTING RECEIPT
        to = time.strftime("DATE:%Y-%m-%d \nTIME:%H:%M:%S", time.localtime())#TIME
        print("PROCESSING RECEIPT...."), time.sleep(3)
        print(f"BANK TRANSACTION RECEIPT:\nACCOUNT ID: #{user_ID}\n{to}\nTOTAL AMOUNT WITHDRAW : -${total_withdraw}\nAMOUNT LEFT: ${withdrawing}")
        
    else:
        withdrawing = A_withdrawn  # RETURN FIRST WITHDRAWN IF USER PICK NO OR ANYTHING ELSE
        print("TOTAL WITHDRAW -> -$", withdrawing)#SHOW USER 1 TOTAL WITHDRAW
        withdrawing = float(amount) - float(withdrawing)#ALRITHMITIC OF THE WITHDRAWING


        #PRINTING RECEIPT
        to = time.strftime("DATE:%Y-%m-%d \nTIME:%H:%M:%S", time.localtime())
        print("PROCESSING RECEIPT...."), time.sleep(3)
        print(f"BANK TRANSACTION RECEIPT:\nACCOUNT ID: #{user_ID}\n{to}\nTOTAL AMOUNT WITHDRAW : -${A_withdrawn}\nAMOUNT LEFT: ${withdrawing}")
        
#______________________________________________________________________________

    with open(ACCOUNT_FILE,"w") as FL:#ADD TO FILE
        FL.write(str(pin)+","+str(withdrawing))

#------------------------------------------------

#========={ DEPOSIT }==========
elif T_transaction == "D":

    # amount = float(amount)  # change amount to an int

    print("PROCESSING REQUEST....\nPLEASE WAIT"), time.sleep(2)

    while True:
        try:
            A_deposit = float(input("HOW MUCH ARE WITHDRAWING TODAY?\nAMOUNT: "))
            break
        except ValueError:
            print("INVALID INPUT")
            continue
    print(f"ADDED -> -${str(A_deposit)}")  # show how much is DEPOSIT

    # _____________________________________________________________________________________________

    ask_t = input("WOULD YOU LIKE TO HAVE ANOTHER DEPOSITING\nYES[Y] OR NO[N]: ").upper()

    if ask_t == "Y":  # IF USER PICK YES T ANOTHER DEPOSIT
        while True:
            try:
                A2_deposit = float(input("HOW MUCH ARE WITHDRAWING TODAY?\nAMOUNT: "))
                break
            except ValueError:
                print("INVALID INPUT")
                continue
        print(f"ADDED -> -${str(A2_deposit)}") # show how much is depositing


        total_deposit = float(A_deposit) + float(A2_deposit)  # RETURN FIRST AND SECOND depositing IF USER PICK YES
        depositing = float(amount) + float(total_deposit)  # SHOW USER 2 TOTAL deposit
        print("TOTAL DEPOSIT -> +$", total_deposit)  # ARITHMETIC OF THE total_deposit

        # PRINTING RECEIPT
        to = time.strftime("DATE:%Y-%m-%d \nTIME:%H:%M:%S", time.localtime())  # TIME
        print("PROCESSING RECEIPT...."), time.sleep(3)
        print(f"BANK TRANSACTION RECEIPT:\nACCOUNT ID: #{user_ID}\n{to}\nTOTAL AMOUNT DEPOSIT : +${total_deposit}\nAMOUNT LEFT: ${depositing}")

    else:
        depositing = A_deposit  # RETURN FIRST deposit IF USER PICK NO OR ANYTHING ELSE
        print("TOTAL DEPOSIT -> +$", depositing)  # SHOW USER 1 TOTAL depositing
        depositing = float(amount) + float(depositing)  # ARITHMETIC OF THE depositing

        to = time.strftime("DATE:%Y-%m-%d \nTIME:%H:%M:%S", time.localtime())  # TIME
        print("PROCESSING RECEIPT...."), time.sleep(3)
        print(f"BANK TRANSACTION RECEIPT:\nACCOUNT ID: #{user_ID}\n{to}\nTOTAL AMOUNT DEPOSIT : +${A_deposit}\nAMOUNT LEFT: ${depositing}")


    # ______________________________________________________________________________

    with open(ACCOUNT_FILE, "w") as FL:#ADD TO FILE
        FL.write(str(pin) + "," + str(depositing))

