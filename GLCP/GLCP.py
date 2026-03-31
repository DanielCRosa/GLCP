import tkinter as tk
import os
import subprocess

# Caminho da pasta onde estão os scripts
pasta = "GEmilly"

def abrir_proteinas():
    caminho = os.path.join(pasta, "GEmilly.py")
    # Abre em um processo separado
    subprocess.Popen(["python3", caminho])

def abrir_regras():
    caminho = os.path.join(pasta, "Regras.py")
    subprocess.Popen(["python3", caminho])

# Criação da janela principal
root = tk.Tk()
root.title("Painel de Controle GLCP")
root.geometry("400x250")
root.minsize(400, 250)
root.configure(bg="#1e1e1e")  # Fundo escuro

# Título
label = tk.Label(root, text="Escolha uma opção:", font=("Helvetica", 18, "bold"), fg="#ffffff", bg="#1e1e1e")
label.pack(pady=25)

# Botões estilizados
btn_proteinas = tk.Button(
    root, 
    text="Proteínas", 
    command=abrir_proteinas,
    width=22,
    height=2,
    font=("Helvetica", 12, "bold"),
    bg="#4caf50",
    fg="#ffffff",
    activebackground="#45a049",
    bd=0,
    relief="raised"
)
btn_proteinas.pack(pady=10)

btn_regras = tk.Button(
    root, 
    text="Regras Lógicas", 
    command=abrir_regras,
    width=22,
    height=2,
    font=("Helvetica", 12, "bold"),
    bg="#2196f3",
    fg="#ffffff",
    activebackground="#1e88e5",
    bd=0,
    relief="raised"
)
btn_regras.pack(pady=10)

root.mainloop()