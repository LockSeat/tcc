import tkinter as tk
from tkinter import ttk, messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageTk
import random
import mysql.connector  # Para interagir com o MySQL

# Função para conectar ao banco de dados MySQL
def conectar_banco():
    try:
        conn = mysql.connector.connect(
            host="localhost",          # Endereço do servidor MySQL
            user="root",               # Seu usuário MySQL
            password="admin",          # Sua senha MySQL
            database="cinema"          # Nome do banco de dados
        )
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Erro", f"Erro ao conectar ao banco de dados: {err}")
        return None

# Função para criar a tabela no banco de dados (caso não exista)
def criar_tabela():
    try:
        conn = conectar_banco()
        if conn is None:
            return

        cursor = conn.cursor()

        # Criar a tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingressos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome_cliente VARCHAR(255),
                filme VARCHAR(255),
                cadeira VARCHAR(10),
                codigo_barras VARCHAR(255)
            )
        ''')

        conn.commit()
        conn.close()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao criar a tabela: {e}")

# Função para inserir dados no banco de dados
def inserir_no_banco(nome_cliente, filme, cadeira, codigo_barras):
    try:
        conn = conectar_banco()
        if conn is None:
            return

        cursor = conn.cursor()

        # Inserir dados na tabela
        cursor.execute('''
            INSERT INTO ingressos (nome_cliente, filme, cadeira, codigo_barras) 
            VALUES (%s, %s, %s, %s)
        ''', (nome_cliente, filme, cadeira, codigo_barras))

        conn.commit()
        conn.close()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar no banco de dados: {e}")

# Função para gerar os códigos de barras para cada cadeira selecionada
def gerar_codigos_de_barras(nome, filme, cadeiras, quantidade):
    try:
        # Validar campos
        if not nome or not filme or not cadeiras or not quantidade.isdigit():
            messagebox.showerror("Erro", "Por favor, preencha todos os campos corretamente!")
            return
        
        quantidade = int(quantidade)
        if quantidade <= 0:
            messagebox.showerror("Erro", "A quantidade deve ser maior que zero!")
            return
        
        if len(cadeiras) != quantidade:
            messagebox.showerror("Erro", f"Você deve escolher exatamente {quantidade} cadeiras!")
            return

        # Gerar o código de barras para cada cadeira selecionada
        for cadeira in cadeiras:
            if cadeira not in [f"A{i}" for i in range(1, 11)]:
                messagebox.showerror("Erro", "Por favor, escolha uma cadeira entre A1 e A10!")
                return

            # Gerar código exclusivo (12 dígitos somente numéricos)
            codigo_base = random.randint(100000, 999999)  # Gera um número aleatório de 6 dígitos
            codigo = f"{codigo_base}{quantidade:03d}{cadeira[1:]}"  # Junta o número aleatório com a quantidade e cadeira
            codigo = codigo.zfill(12)  # Garante 12 dígitos

            # Criar código de barras
            ean = barcode.get('ean13', codigo, writer=ImageWriter())
            filename = f"codigo_de_barras_{codigo}"
            filepath = ean.save(filename)

            # Inserir dados no banco de dados
            inserir_no_banco(nome, filme, cadeira, codigo)

            # Mostrar código de barras gerado
            mostrar_codigo_de_barras(filepath, cadeira)
            messagebox.showinfo("Sucesso", f"Código de barras gerado para a cadeira {cadeira}: {filename}.png")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao gerar o código de barras: {e}")

# Função para exibir o código de barras gerado
def mostrar_codigo_de_barras(filepath, cadeira):
    try:
        img = Image.open(filepath)
        img = img.resize((300, 100), Image.Resampling.LANCZOS)  # Alteração para o método correto
        img_tk = ImageTk.PhotoImage(img)
        
        # Adicionar o código de barras à interface
        lbl_codigo = tk.Label(root, text=f"Código de barras para a cadeira {cadeira}")
        lbl_codigo.pack(pady=5)
        
        lbl_img = tk.Label(root)
        lbl_img.config(image=img_tk)
        lbl_img.image = img_tk
        lbl_img.pack(pady=5)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível exibir o código de barras: {e}")

# Função para atualizar a seleção de cadeiras conforme a quantidade de ingressos
def atualizar_seletor_cadeiras():
    try:
        quantidade = int(entry_quantidade.get())
        if quantidade <= 0:
            messagebox.showerror("Erro", "A quantidade deve ser maior que zero!")
            return
        
        # Atualizar os cadeirões
        cadeiras_disponiveis = [f"A{i}" for i in range(1, 11)]
        cadeiras_selecionadas = []

        # Limpar comboboxes de cadeiras já existentes
        for widget in frame_cadeiras.winfo_children():
            widget.destroy()

        # Criar novos comboboxes para seleção de cadeiras
        for i in range(quantidade):
            lbl_cadeira = tk.Label(frame_cadeiras, text=f"Cadeira {i+1}:")
            lbl_cadeira.grid(row=i, column=0, padx=5, pady=5)
            combo_cadeira = ttk.Combobox(frame_cadeiras, values=cadeiras_disponiveis)
            combo_cadeira.grid(row=i, column=1, padx=5, pady=5)
            combo_cadeira.set("A1")
            cadeiras_selecionadas.append(combo_cadeira)
        
        # Salvar as cadeiras selecionadas
        btn_finalizar.config(command=lambda: finalizar_compra(cadeiras_selecionadas))

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao atualizar seletores de cadeiras: {e}")

# Função para finalizar a compra
def finalizar_compra(cadeiras_selecionadas):
    nome = entry_nome.get()
    filme = combo_filme.get()
    quantidade = entry_quantidade.get()
    cadeiras = [cadeira.get() for cadeira in cadeiras_selecionadas]

    gerar_codigos_de_barras(nome, filme, cadeiras, quantidade)

# Configuração da janela principal
root = tk.Tk()
root.title("Simulador de Compra de Ingressos de Cinema")
root.geometry("500x700")

# Chamar a função para criar a tabela no banco de dados
criar_tabela()

# Título
lbl_titulo = tk.Label(root, text="Simulador de Compra de Ingressos", font=("Arial", 16, "bold"))
lbl_titulo.pack(pady=10)

# Entrada para o nome do cliente
frame_nome = tk.Frame(root)
frame_nome.pack(pady=5)
lbl_nome = tk.Label(frame_nome, text="Nome do Cliente:")
lbl_nome.pack(side=tk.LEFT, padx=5)
entry_nome = tk.Entry(frame_nome, width=30)
entry_nome.pack(side=tk.LEFT)

# Combobox para o filme
frame_filme = tk.Frame(root)
frame_filme.pack(pady=5)
lbl_filme = tk.Label(frame_filme, text="Selecione o Filme:")
lbl_filme.pack(side=tk.LEFT, padx=5)
combo_filme = ttk.Combobox(frame_filme, values=["O Rei Leão", "Vingadores", "Batman", "Superman", "Frozen"])
combo_filme.pack(side=tk.LEFT)
combo_filme.set("O Rei Leão")  # Filme padrão

# Entrada para quantidade
frame_quantidade = tk.Frame(root)
frame_quantidade.pack(pady=5)
lbl_quantidade = tk.Label(frame_quantidade, text="Quantidade de Ingressos:")
lbl_quantidade.pack(side=tk.LEFT, padx=5)
entry_quantidade = tk.Entry(frame_quantidade, width=10)
entry_quantidade.pack(side=tk.LEFT)
entry_quantidade.bind("<KeyRelease>", lambda event: atualizar_seletor_cadeiras())

# Frame para seleção dinâmica de cadeiras
frame_cadeiras = tk.Frame(root)
frame_cadeiras.pack(pady=10)

# Botão para finalizar a compra
btn_finalizar = tk.Button(root, text="Finalizar Compra", command=lambda: finalizar_compra([]), bg="blue", fg="white")
btn_finalizar.pack(pady=20)

# Iniciar o loop principal
root.mainloop()
