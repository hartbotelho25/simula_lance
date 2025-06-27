import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

def format_reais(valor):
    return f"R$ {int(round(valor)):,}".replace(",", ".")

# Função para formatar o input do valor da carta com pontos de milhar
def format_input_valor(valor_str):
    if not valor_str:
        return ""
    # Remove todos os caracteres não numéricos, exceto a vírgula (que será substituída por ponto)
    valor_limpo = valor_str.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        valor_float = float(valor_limpo)
        # Formata para inteiro para evitar casas decimais indesejadas na formatação de milhar
        return f"{int(valor_float):,}".replace(",", ".")
    except ValueError:
        return valor_str # Retorna o valor original se não for um número válido

st.set_page_config(page_title="Simulador de Consórcio", layout="wide")
st.markdown("<h6 style='text-align: center; color: gray;'>Desenvolvido por Hart Botelho</h6>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>Simulador de Consórcio</h1>", unsafe_allow_html=True)
st.markdown("### 📋 Informações da Simulação")

col_form, col_lance = st.columns([2, 1])

with col_form:
    tipo = st.selectbox("Tipo de Bem", ["Imóvel", "Veículo"])
    col1, col2 = st.columns(2)
    with col1:
        # Usando um callback para formatar o input
        valor_carta_input = st.text_input("Valor da Carta (R$)", value="100.000", key="valor_carta_raw")
        valor_carta_formatado = format_input_valor(valor_carta_input)
        st.session_state.valor_carta = valor_carta_formatado # Armazena o valor formatado para uso

        prazo = st.number_input("Prazo (meses)", min_value=1, step=1, value=120)
    with col2:
        fundo_reserva = st.number_input("Fundo de Reserva (%)", min_value=0, step=1, value=3)
        taxa_admin = st.number_input("Taxa de Administração (%)", min_value=0, step=1, value=15)
        # NOVO CAMPO: Taxa de Juros Anual para aplicação
        taxa_juros_anual = st.number_input("Taxa de Juros Anual da Aplicação (%)", min_value=0.0, step=0.1, value=6.0, format="%.1f")


    calcular = st.button("Calcular", use_container_width=True)

with col_lance:
    try:
        # Usa o valor armazenado em session_state para garantir que está formatado corretamente
        valor_carta_float_preview = float(st.session_state.valor_carta.replace(".", "").replace(",", "."))
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

    # Calcula o 'valor da carta' ajustado para que o crédito líquido após o lance embutido seja valor_carta_float_preview
    if (1 - (lance_embutido / 100)) > 0:
        valor_carta_ajustado_com_embutido_preview = valor_carta_float_preview / (1 - (lance_embutido / 100))
    else:
        valor_carta_ajustado_com_embutido_preview = valor_carta_float_preview

    valor_lance_proprio_com = valor_carta_ajustado_com_embutido_preview * (lance_proprio_com / 100)
    valor_lance_embutido_com = valor_carta_ajustado_com_embutido_preview * (lance_embutido / 100)

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

    # Destaque para a base de cálculo da carta ajustada
    st.markdown(f"### <p style='text-align: center; color: #2c3e50;'>Base de Cálculo (Carta Ajustada): {format_reais(valor_carta_ajustado_com_embutido_preview)}</p>", unsafe_allow_html=True)
    st.caption(f"✨ Valor Líquido de Crédito Desejado: {format_reais(valor_carta_float_preview)}")


# Ajuste dos limites do lance embutido
limite_embutido = 0.50 if tipo == "Imóvel" else 0.30
erro_embutido = False
if lance_embutido / 100 > limite_embutido:
    st.error(f"🚫 O lance embutido informado ({lance_embutido}%) ultrapassa o limite permitido para {tipo.lower()}. 👉 Para {tipo.lower()}, o máximo permitido é {int(limite_embutido * 100)}%. Corrija o valor para continuar.")
    erro_embutido = True
elif lance_embutido == 100:
    st.error("🚫 O lance embutido não pode ser 100%, pois não haveria valor de carta para ajuste.")
    erro_embutido = True

if calcular and not erro_embutido:
    try:
        # Usa o valor armazenado em session_state para garantir que está formatado corretamente
        valor_carta_float = float(st.session_state.valor_carta.replace(".", "").replace(",", "."))

        taxa_total = taxa_admin + fundo_reserva

        # Cálculos para "SEM LANCE EMBUTIDO"
        total_sem_lance = valor_carta_float * (1 + taxa_total / 100)
        parcela_sem_lance = total_sem_lance / prazo

        valor_lance_padrao = valor_carta_float * (lance_proprio_sem / 100)
        saldo_apos_padrao = total_sem_lance - valor_lance_padrao
        parcela_padrao = saldo_apos_padrao / prazo

        # Calcula o 'valor da carta' ajustado para o cenário "COM LANCE EMBUTIDO"
        if (1 - (lance_embutido / 100)) > 0:
            valor_carta_ajustado_para_embutido = valor_carta_float / (1 - (lance_embutido / 100))
        else:
            valor_carta_ajustado_para_embutido = valor_carta_float


        total_corrigido = valor_carta_ajustado_para_embutido * (1 + taxa_total / 100)
        parcela_sem_contemplacao_embutido = total_corrigido / prazo

        valor_lance_proprio_com_calc = valor_carta_ajustado_para_embutido * (lance_proprio_com / 100)
        valor_lance_embutido_com_calc = valor_carta_ajustado_para_embutido * (lance_embutido / 100)
        valor_total_lance_calc = valor_lance_proprio_com_calc + valor_lance_embutido_com_calc

        saldo_apos_contemplacao = total_corrigido - valor_total_lance_calc
        parcela_contemplacao_total = saldo_apos_contemplacao / prazo

        taxa_mensal_total = taxa_total / prazo
        taxa_anual_total = taxa_mensal_total * 12

        # Diferença de parcela pós-contemplação ajustada
        diferenca_parcela_pos_contemplacao = parcela_contemplacao_total - parcela_padrao

        # --- NOVOS CÁLCULOS PARA VANTAGEM FINANCEIRA DA APLICAÇÃO (SOMENTE SEM LANCE EMBUTIDO) ---
        taxa_juros_mensal = (1 + taxa_juros_anual / 100)**(1/12) - 1

        # Cenário Sem Lance Embutido
        saldo_para_aplicar_sem_lance = valor_carta_float - valor_lance_padrao
        rendimento_aplicacao_sem_lance = saldo_para_aplicar_sem_lance * ((1 + taxa_juros_mensal)**prazo)
        ganho_aplicacao_sem_lance = rendimento_aplicacao_sem_lance - saldo_para_aplicar_sem_lance
        encargos_consorcio_sem_lance = valor_carta_float * (taxa_total / 100)
        vantagem_liquida_sem_lance = ganho_aplicacao_sem_lance - encargos_consorcio_sem_lance
        # --- FIM DOS NOVOS CÁLCULOS ---


        resultado = f"""
Simulação de Consórcio - {tipo.upper()}

[1] SEM LANCE EMBUTIDO
Valor da carta: {format_reais(valor_carta_float)}
Parcela mensal (sem contemplação): {format_reais(parcela_sem_lance)}
Parcela com contemplação ({lance_proprio_sem}%): {format_reais(parcela_padrao)}
Valor do lance: {format_reais(valor_lance_padrao)}
Prazo: {prazo} meses

[2] COM LANCE EMBUTIDO
Valor Líquido de Crédito Desejado: {format_reais(valor_carta_float)}
Valor da carta AJUSTADA para Lance Embutido: {format_reais(valor_carta_ajustado_para_embutido)}
Parcela mensal (sem contemplação): {format_reais(parcela_sem_contemplacao_embutido)}
Parcela com contemplação ({lance_proprio_com + lance_embutido}%): {format_reais(parcela_contemplacao_total)}
Lance Próprio: {format_reais(valor_lance_proprio_com_calc)}
Lance Embutido: {format_reais(valor_lance_embutido_com_calc)}
Valor TOTAL do lance: {format_reais(valor_total_lance_calc)}
Prazo: {prazo} meses

[3] ANÁLISE DE CUSTO
Total de taxas: {taxa_total:.2f}%
Taxa equivalente mensal: {taxa_mensal_total:.2f}%
Taxa equivalente anual: {taxa_anual_total:.2f}%
Diferença entre parcelas pós-contemplação - (Com Lance Embutido - Sem Lance): {format_reais(diferenca_parcela_pos_contemplacao)}

[4] ANÁLISE DE VANTAGEM FINANCEIRA COM APLICAÇÃO (Taxa de Juros Anual: {taxa_juros_anual:.2f}%)
    Cenário Sem Lance Embutido:
        Valor para aplicar: {format_reais(saldo_para_aplicar_sem_lance)}
        Rendimento da aplicação: {format_reais(ganho_aplicacao_sem_lance)}
        Vantagem líquida: {format_reais(vantagem_liquida_sem_lance)}
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
        st.text_area("Resumo", resultado.strip(), height=800) # Aumentei a altura para acomodar o novo conteúdo
    except Exception as e:
        st.error(f"Erro no cálculo: {e}")
