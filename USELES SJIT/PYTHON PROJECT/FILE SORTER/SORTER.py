import shutil,os,dotenv,time


#INPUT FOLDERS
unsorted_pth="UNSORTED_FILES"
#FILE_GUIDE= r"C:\Users\CJ\OneDrive\Desktop\PYTHON PROJECT\FILE SORTER\FILE_GUIDE.env" #fr"C:\Users\{os.}\Desktop\PYTHON PROJECT\FILE SORTER\FILE_GUIDE.env"
dot_guide = dotenv.dotenv_values("FILE_GUIDE.env")


#PATH AND EXTENSION LIST VARIABLES
Xtension =[]
PTH = []

#_________________________|CHECK IF USER ENTERS UNSORTED_FOLDER|_________________________
def FOLDER_CHECK():
    while True:
        global unsorted_pth
        unsorted_pth = input("DO YOU WANT INPUT NEW UNSORTED PATH\nENTER [D\d] for default\nENTER ->").strip('"')


        if unsorted_pth == "d" or unsorted_pth == "D":
            unsorted_pth = "UNSORTED_FILES"
            print(f"DEFAULT FOLDER: {unsorted_pth}"),time.sleep(1.3)
            #break

        if os.path.exists(unsorted_pth):
            #print(f"ENTERED: {unsorted_pth}\nPATH EXIST\nPROCESSING PATH"),time.sleep(1.3)
            #return  unsorted_pth
            break

        print(F"{unsorted_pth}\nPATH DOES NOT EXIST"),time.sleep(1.3)
        continue

#_________________________|CHECK IF USER WANT TO CHANGE EXISTING or ENTERS NEW SORTED_FOLDER|_________________________

def change_an_add_paths():
#ASKING FOR CHOICE
    ask = input("DO YOU WANT TO ADD OR CHANGE EXITING PATH\nADD NEW PATH[A] : CHANGE EXISTING PATH[C] : REMOVE PATH [R]: NOT RIGHT NOW [N]\nENTER  ->").upper()

#__________________________________ADD A NEW FILE PATH___________________________________________________
    if ask == "A":#IF USER PICKS A FOR ADDING A NEW PATH
        dot_exten = input("PLEASE INPUT EXTENSION TYPE\nENTER ->").strip(".")#FOR ADDING FILE EXTENSION TO FILE
        dir_path = input("PLEASE INPUT C: PATH\nENTER ->")#FOR ADDING DIRECTORY TO FILE

        with open("FILE_GUIDE.env","a") as add_path:#OPEN THE FILE
            add_path.write(f"\n.{dot_exten}={dir_path}")#ADD TO FILE

#_________________________________CHANGING EXISTING FILE PATH____________________________________________________
    elif ask == "C":
        #SHOWING PATHS
        Its = []
        print("---OPTIONS---")
        for xt, ppth in dot_guide.items():
            Its.append(xt.strip("."))#ADD DISPLAYING PATH LIST

            print(len(Its), "|", xt, "->", ppth)  # DISPLAYING PATHS
            time.sleep(1)


        Picked_xten = input("CHOSE THE EXTENSION YOU WANT TO CHANGE PATH FOR\nENTER:").strip(".")
        while len(Picked_xten) == 0 : Picked_xten = input("CHOSE AN EXTENSION FROM THE OPTION\nENTER:").strip(".")
        while  Picked_xten not in Its: Picked_xten = input("CHOSE AN EXTENSION FROM THE OPTION ABOVE\nENTER:").strip(".")

        #___________________________________________________________________________________________________________________________
        Picked_pth = input("CHOSE AN PATH\nENTER:")
        print("VERIFYING ENTER PATH,PLEASE WAIT..."),time.sleep(1.3)
        while len(Picked_pth) == 0 : Picked_pth = input("ENTER NEW PATH\nENTER:").strip('"').strip("'")
        while not os.path.exists(Picked_pth):
            Picked_pth = input("PATH DOES NOT EXIST\nENTER NEW PATH\nENTER:").strip('"').strip("'")
            print("VERIFYING ENTER PATH,PLEASE WAIT..."),time.sleep(1.3)

        print("VERIFIED DIRECTORY PATH")

        #___________________________________________________________________________________________________________________________

        update_lines = []

        for change_xten, change_pth in dot_guide.items():#OPEN ENV FILE TO GET VARIABLES

            if change_xten.startswith(f".{Picked_xten}"):#SEARCH FOR THAT EXTENSION
                change_pth = change_pth.replace(change_pth,Picked_pth)

            update_lines.append(f"{change_xten} = {change_pth}\n")#ADD TO ENV CHANGE LIST


        with open("FILE_GUIDE.env", "w") as change_path:
            change_path.writelines(update_lines)#ADD TO ENV FILE

#_________________________________REMOVING EXISTING FILE PATH____________________________________________________
    elif ask == "R":
        # SHOWING PATHS
        Its = []
        print("---OPTIONS---")
        for xt, ppth in dot_guide.items():
            Its.append(xt.strip("."))  # ADD DISPLAYING PATH LIST

            print(len(Its), "|", xt, "->", ppth)  # DISPLAYING PATHS
            time.sleep(1)

        #REMOVING PATH --------------------
        Picked_xten = input("CHOSE THE EXTENSION YOU WANT TO REMOVE PATH FOR\nENTER:").strip(".")
        while len(Picked_xten) == 0 : Picked_xten = input("CHOSE AN EXTENSION FROM THE OPTION\nENTER:").strip(".")
        while  Picked_xten not in Its: Picked_xten = input("CHOSE AN EXTENSION FROM THE OPTION ABOVE\nENTER:").strip(".")

        Read_lines = []
        Picked_xten = "."+Picked_xten

        for remove_xten, remove_pth in dot_guide.items():  # OPEN ENV FILE TO GET VARIABLES
            Read_lines.append(f"{remove_xten} = {remove_pth}\n")#ADD TO LIST PATH LIST

            if remove_xten.startswith(Picked_xten):#FIND THAT PATH WITH THAT EXTENSION
                Read_lines.remove(f"{remove_xten} = {remove_pth}\n")#FIND THAT PATH WITH THAT EXTENSION


        with open("FILE_GUIDE.env", "w") as Remove_path:
            Remove_path.writelines(Read_lines)#REMOVE PATH FROM ENV FILE

             # ADD TO ENV CHANGE LIST

# _________________________________IF USER DOES NOT WANT TO DO ANYTHING____________________________________________________
    else:
        print("OK")

#_________________________|SEARCH FOR THAT FOLDER AND MOVE ALL FILE WITH THAT EXTENSION|__________________________
def movein(xTEN,MOV):#FUNCTION THAT SEARCH FOR THAT FOLDER AND MOVE ALL FILE WITH THAT EXTENSION
    if os.path.exists(MOV):
        pass
    else:
        print(f"PATH:{MOV}\nPATH DOES NOT EXIST"),quit()


    for find_file_name in os.listdir(unsorted_pth):#LOOP FILE NAME

        file_dirt = os.path.join(unsorted_pth,find_file_name)#--FIND FILE PATH

        print("LOOKING FOR FILES......"),time.sleep(1.7)


        if file_dirt.endswith(xTEN):

            print(f"{len(MOV),xTEN} WERE FOUND")


            if input("ARE SURE YOU WANT TO MOVE: [Y]/[N]").upper() == "Y":#CHECK IF USER IS SHOULD ABOUT MOVING
                print("PROCESSING REQUEST..."), time.sleep(1)

                print(file_dirt," MOVE TO ",MOV),time.sleep(1.7)#

                #MOVE FILE WITH THAT SPECIFIC EXTENSION
                shutil.move(file_dirt,MOV)
            else:
                print("PROCESSING REQUEST..."),time.sleep(1)
                print("NOW QUITING")
                quit()

        else:
            print("NO FILES WITH ADDED EXTENSION ARE THERE")

#_________________________|SEARCH FOR THAT FOLDER AND MOVE SELECTED FILE WITH THAT EXTENSION|__________________________
def SELECTIVE_move(MOV_TO_PTH,unsorted_file):#FUNCTION THAT SEARCH FOR THAT FOLDER AND MOVE ALL FILE WITH THAT EXTENSION
#_____________
    if os.path.exists(MOV_TO_PTH):
        pass
    else:
        print(f"PATH:{MOV_TO_PTH}\nPATH DOES NOT EXIST"),quit()

#_____________
    if os.path.exists(unsorted_file):
        pass
    else:
        print(f"PATH:{unsorted_file}\nPATH DOES NOT EXIST"),quit()



#_____________________________________________________________________

    print("LOOKING FOR FILES......"),time.sleep(1.7)


    print(unsorted_file, " MOVE TO ", MOV_TO_PTH), time.sleep(1)  #
    shutil.move(unsorted_file, MOV_TO_PTH)
    # _______________


P_move = input("MULTI[M] -> DEFAULT MOVE FROM ADDED FILE\nSELECTIVE [S]-> SELECT CERTAIN TO MOVE\nDO YOU WANT SELECTIVE OR MULTI MOVE FILE:").upper()

if P_move == "M":
    change_an_add_paths()


    ask_move = input("DO WANT VARY EXTENSION [V] OR SINGLE EXTENSION MOVE [S]\nENTER ->").upper()

    #------VARY MOVE
    if ask_move == "V":

        FOLDER_CHECK()
        #_________________________|ADD EXTENSION FROM ENV FILE TO XTENSION LIST TO LOOP|__________________________
        for xten,pth in dot_guide.items():
           Xtension.append(xten)#ADD EXTENSION TO LIST
           PTH.append(pth)#ADD PATH TO LIST


        #_________________________|LOOP LIST XTENSION LIST |__________________________
        for x_loop,pth_loop in zip(Xtension,PTH):
            print("FILE TYPE -->" + x_loop)
            movein(x_loop,pth_loop)#CALL FUNCTION
            print("="*300)

    # ------SINGLE EXTENSION MOVE
    elif ask_move == "S":
        #----UNSORTED FOLDER
        while True:
            unsorted_pth=input("INPUT NEW UNSORTED PATH\nENTER ->").strip('"')
            while len(unsorted_pth) == 0: unsorted_pth=input("INPUT NEW UNSORTED PATH\nENTER ->").strip('"')

            if os.path.exists(unsorted_pth):
                break
            print(F"{unsorted_pth}\nPATH DOES NOT EXIST"), time.sleep(1.3)
            continue


        # -----EXTENSION
        x_ten = input("ADD PICK YOUR EXTENSION\nENTER:").strip(".")
        x_ten = "."+x_ten


        #-----MOVING PATH
        while True:
            pa_th = input("ADD PICK YOUR MOVING TO\nENTER:").strip('"')
            while len(pa_th) == 0: pa_th = input("ADD PICK YOUR MOVING TO\nENTER:").strip('"')

            if os.path.exists(pa_th):
                break
            print(F"{pa_th}\nPATH DOES NOT EXIST"), time.sleep(1.3)
            continue


        movein(x_ten,pa_th)

elif  P_move == "S":#SELECTIVE MOVING

    #-----FOR ADD EXTENSION
    while True:
        xten = input("WHAT THE UNSORTED FILE YOUR ADDING\nENTER:")
        if xten =="N" or xten =="n":
            break
        else:
            Xtension.append(xten)
    # -----FOR ADD PATH
    while True:
        pth = input("WHAT THE FOLDER PATH OR EXTENSION ARE YOU ADDING\nENTER:")
        if pth =="N" or pth =="n":
            break
        else:
            PTH.append(pth)


    #-----FOR DISPLAYING FILES
    lts = []
    for N, c in zip(PTH, Xtension):
        lts.append(N)
        print(len(lts),"|",N,"->", c)


    #-----REMOVE PATH AND EXTENSION
    while True:
        rem = input("WHAT PATH ARE YOU REMOVING[SELECT A NUMBER#]\nENTER N TO STOP\nENTER:")

        if rem =="N" or rem =="n":
            break
        else:
            print(PTH[int(rem)],Xtension[int(rem)])
            PTH.remove(PTH[int(rem)])
            Xtension.remove(PTH[int(rem)])




    #---CALL FUNC
    for x_loop, pth_loop in zip(Xtension, PTH):

        SELECTIVE_move(pth_loop,x_loop)





# STUFF ADDING:
#FIX SINGLE SELECT