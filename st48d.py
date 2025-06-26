import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

def format_reais(valor):
    return f"R$ {int(round(valor)):,}".replace(",", ".")

st.set_page_config(page_title="Simulador de Consórcio", layout="wide")
st.markdown("<h6 style='text-align: center; color: gray;'>Desenvolvido por Hart Botelho</h6>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>Simulador de Consórcio</h1>", unsafe_allow_html=True)
st.markdown("### 📋 Informações da Simulação")

col_form, col_lance = st.columns([2, 1])

with col_form:
    tipo = st.selectbox("Tipo de Bem", ["Imóvel", "Veículo"])
    col1, col2 = st.columns(2)
    with col1:
        valor_carta = st.text_input("Valor da Carta (R$)", value="100.000,00")
        prazo = st.number_input("Prazo (meses)", min_value=1, step=1, value=120)
    with col2:
        fundo_reserva = st.number_input("Fundo de Reserva (%)", min_value=0, step=1, value=3)
        taxa_admin = st.number_input("Taxa de Administração (%)", min_value=0, step=1, value=15)

    calcular = st.button("Calcular", use_container_width=True)

with col_lance:
    try:
        valor_carta_float_preview = float(valor_carta.replace(".", "").replace(",", "."))
    except:
        valor_carta_float_preview = 0.0

    st.markdown("### 🎯 Sem Lance Embutido")
    col_sem1, col_sem2 = st.columns([1, 1])
    with col_sem1:
        lance_proprio_sem = st.number_input("Lance Próprio (%)", min_value=0, max_value=100, step=1, value=10, key="sem_lance")
    with col_sem2:
        valor_lance_proprio_sem = valor_carta_float_preview * (lance_proprio_sem / 100)
        st.markdown(f"**{format_reais(valor_lance_proprio_sem)}**")

    st.markdown("---")
    st.markdown("### 🎯 Com Lance Embutido")

    col_com1, col_com2 = st.columns([1, 1])
    with col_com1:
        lance_proprio_com = st.number_input("Lance Próprio (%)", min_value=0, max_value=100, step=1, value=10, key="com_lance_proprio")
    with col_com2:
        lance_embutido = st.number_input("Lance Embutido (%)", min_value=0, max_value=100, step=1, value=20, key="com_lance_embutido")

    valor_corrigido_preview = valor_carta_float_preview * (1 + (lance_embutido / 100))
    valor_lance_proprio_com = valor_corrigido_preview * (lance_proprio_com / 100)
    valor_lance_embutido_com = valor_corrigido_preview * (lance_embutido / 100)

    col_com3, col_com4 = st.columns([1, 1])
    with col_com3:
        st.markdown("Lance Próprio (R$)")
        st.markdown(f"**{format_reais(valor_lance_proprio_com)}**")
    with col_com4:
        st.markdown("Lance Embutido (R$)")
        st.markdown(f"**{format_reais(valor_lance_embutido_com)}**")

    valor_total_lance_com = valor_lance_proprio_com + valor_lance_embutido_com
    total_lance_pct = lance_proprio_com + lance_embutido
    st.markdown(f"💰 **Total do Lance com Embutido: {int(total_lance_pct)}% — {format_reais(valor_total_lance_com)}**")
    st.caption(f"📌 Base de cálculo (carta corrigida): {format_reais(valor_corrigido_preview)}")

limite_embutido = 0.3 if tipo == "Imóvel" else 0.5
erro_embutido = False
if lance_embutido / 100 > limite_embutido:
    st.error(f"🚫 O lance embutido informado ({lance_embutido}%) ultrapassa o limite permitido para {tipo.lower()}. 👉 Para {tipo.lower()}, o máximo permitido é {int(limite_embutido * 100)}%. Corrija o valor para continuar.")
    erro_embutido = True

if calcular and not erro_embutido:
    try:
        valor_carta_float = float(valor_carta.replace(".", "").replace(",", "."))
        valor_corrigido = valor_carta_float * (1 + (lance_embutido / 100))
        taxa_total = taxa_admin + fundo_reserva

        total_sem_lance = valor_carta_float * (1 + taxa_total / 100)
        parcela_sem_lance = total_sem_lance / prazo

        valor_lance_padrao = valor_carta_float * (lance_proprio_sem / 100)
        saldo_apos_padrao = total_sem_lance - valor_lance_padrao
        parcela_padrao = saldo_apos_padrao / prazo

        total_corrigido = valor_corrigido * (1 + taxa_total / 100)
        parcela_sem_contemplacao_embutido = total_corrigido / prazo

        valor_total_lance = valor_corrigido * ((lance_proprio_com + lance_embutido) / 100)
        saldo_apos_contemplacao = total_corrigido - valor_total_lance
        parcela_contemplacao_total = saldo_apos_contemplacao / prazo

        taxa_mensal = taxa_total / prazo
        taxa_anual = taxa_mensal * 12

        diferenca_parcela_pos_contemplacao = parcela_padrao - parcela_contemplacao_total

        resultado = f"""
Simulação de Consórcio - {tipo.upper()}

[1] SEM LANCE EMBUTIDO
Valor da carta: {format_reais(valor_carta_float)}
Parcela mensal (sem contemplação): {format_reais(parcela_sem_lance)}
Parcela com contemplação ({lance_proprio_sem}%): {format_reais(parcela_padrao)}
Valor do lance: {format_reais(valor_lance_proprio_sem)}
Prazo: {prazo} meses

[2] COM LANCE EMBUTIDO
Valor da carta atualizada: {format_reais(valor_corrigido)}
Parcela mensal (sem contemplação): {format_reais(parcela_sem_contemplacao_embutido)}
Parcela com contemplação ({lance_proprio_com + lance_embutido}%): {format_reais(parcela_contemplacao_total)}
Valor do lance: {format_reais(valor_total_lance_com)}
Prazo: {prazo} meses

[3] ANÁLISE DE CUSTO
Total de taxas: {taxa_total:.2f}%
Taxa equivalente mensal: {taxa_mensal:.2f}%
Taxa equivalente anual: {taxa_anual:.2f}%
Diferença parcela pós-contemplação (Sem Lance - Com Lance Embutido): {format_reais(diferenca_parcela_pos_contemplacao)}
        """

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        largura, altura = A4
        c.setFillColorRGB(0.18, 0.24, 0.31)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(40, altura - 50, "📊 Simulação de Consórcio")
        c.setFillColorRGB(0.33, 0.33, 0.33)
        c.setFont("Helvetica", 12)
        c.drawString(40, altura - 70, "Relatório Gerado pelo Simulador")
        c.setFillColorRGB(0, 0, 0)
        textobject = c.beginText(40, altura - 100)
        textobject.setFont("Helvetica", 10)
        for linha in resultado.strip().split("\n"):
            if linha.startswith("["):
                textobject.setFont("Helvetica-Bold", 11)
            elif ":" in linha:
                textobject.setFont("Helvetica", 10)
            textobject.textLine(linha)
        c.drawText(textobject)
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawString(40, 30, "Desenvolvido por Hart Botelho | Simulador de Consórcio")
        c.showPage()
        c.save()
        buffer.seek(0)

        st.download_button("📥 Download PDF", buffer, file_name="simulacao_consorcio.pdf", mime="application/pdf")
        st.markdown("### 🧾 Resultado da Simulação")
        st.text_area("Resumo", resultado.strip(), height=480)
    except Exception as e:
        st.error(f"Erro no cálculo: {e}")
