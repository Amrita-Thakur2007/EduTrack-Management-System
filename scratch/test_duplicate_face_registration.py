import os
import sys
import tkinter as tk
import time
import pickle
import numpy as np
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DBManager
from face_attendance.face_registration import FaceRegisterWindow

messages_info = []
messages_warning = []
messages_error = []

messagebox.showinfo = lambda title, msg: messages_info.append((title, str(msg)))
messagebox.showwarning = lambda title, msg: messages_warning.append((title, str(msg)))
messagebox.showerror = lambda title, msg: messages_error.append((title, str(msg)))

def test_duplicate_face():
    print("=== TESTING DUPLICATE FACE REGISTRATION PREVENTION ===")
    
    db_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"test_dup_face_{int(time.time())}.db")
    if os.path.exists(db_file):
        os.remove(db_file)
    db = DBManager(db_file)
    
    root = tk.Tk()
    root.withdraw()
    
    # 1. Create two students in DB: Amrita and Anandi
    u_amrita = db.create_user("amrita", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_AMRITA",
        "name": "Amrita",
        "education_type": "School",
        "school_name": "SKV No. 1",
        "current_class": "10",
        "section": "A"
    }, u_amrita)
    
    u_anandi = db.create_user("anandi", "Pass1234", "Student")
    db.add_student({
        "student_id": "STU_ANANDI",
        "name": "Anandi",
        "education_type": "School",
        "school_name": "SKV No. 1",
        "current_class": "10",
        "section": "B"
    }, u_anandi)
    
    # Register Amrita's face
    np.random.seed(100)
    amrita_face = (np.random.rand(100, 100) * 255).astype(np.uint8)
    db.save_face_encoding("STU_AMRITA", pickle.dumps(amrita_face))
    print("[PASS] Step 1: Amrita's face is registered in DB.")
    
    # Step 2: Now try to register the SAME (Amrita's) face for Anandi
    messages_error.clear()
    messages_info.clear()
    
    FaceRegisterWindow._start_camera = lambda self: None
    reg_win = FaceRegisterWindow(root, "STU_ANANDI", "Anandi", db)
    reg_win.captured_encoding = amrita_face
    reg_win.save_face()
    reg_win.destroy()
    
    # Verification: Must have shown error and NOT saved for Anandi!
    assert len(messages_error) > 0, "Duplicate face error must be triggered!"
    print("[PASS] Step 2: Duplicate face blocked with error message:", messages_error[0][1])
    assert "already registered to another person" in messages_error[0][1]
    assert "Amrita" in messages_error[0][1]
    
    anandi_face_in_db = db.get_face_encoding("STU_ANANDI")
    assert anandi_face_in_db is None, "Anandi face must NOT be saved when duplicate face is presented!"
    print("[PASS] Step 3: Database confirmed Anandi face was NOT registered with Amrita's duplicate face!")
    
    # Step 3: Now try to register a UNIQUE face for Anandi
    messages_error.clear()
    messages_info.clear()
    
    np.random.seed(200)
    anandi_face = (np.random.rand(100, 100) * 255).astype(np.uint8)
    
    reg_win2 = FaceRegisterWindow(root, "STU_ANANDI", "Anandi", db)
    reg_win2.captured_encoding = anandi_face
    reg_win2.save_face()
    reg_win2.destroy()
    
    assert len(messages_error) == 0, "No error should occur for unique face!"
    assert len(messages_info) > 0, "Success dialog must be shown for unique face!"
    anandi_face_in_db = db.get_face_encoding("STU_ANANDI")
    assert anandi_face_in_db is not None, "Anandi unique face must be saved!"
    print("[PASS] Step 4: Anandi unique face registered successfully!")
    
    try:
        root.destroy()
    except Exception:
        pass
        
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass
            
    print("\nALL DUPLICATE FACE REGISTRATION TESTS PASSED 100%!")

if __name__ == "__main__":
    test_duplicate_face()
