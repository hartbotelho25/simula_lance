import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def format_reais(valor):
    return f"R$ {int(round(valor)):,}".replace(",", ".")

# Função para formatar o input do valor da carta com pontos de milhar
def format_input_valor(valor_str):
    if not valor_str:
        return ""
    valor_limpo = valor_str.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        valor_float = float(valor_limpo)
        return f"{int(valor_float):,}".replace(",", ".")
    except ValueError:
        return valor_str

st.set_page_config(page_title="Simulador de Consórcio", layout="wide")
st.markdown("<h6 style='text-align: center; color: gray;'>Desenvolvido por Hart Botelho</h6>", unsafe_allow_html=True)
st.markdown("<h6 style='text-align: center; color: gray; font-size: small;'>Versão 002 | Última atualização em 31/07/2025</h6>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>Simulador de Consórcio</h1>", unsafe_allow_html=True)
st.markdown("### 📋 Informações da Simulação")

col_form, col_lance = st.columns([2, 1])

with col_form:
    tipo = st.selectbox("Tipo de Bem", ["Imóvel", "Veículo"])
    col1, col2 = st.columns(2)
    with col1:
        valor_carta_input = st.text_input("Valor do crédito desejado (R$)", value="100.000", key="valor_carta_raw")
        valor_carta_formatado = format_input_valor(valor_carta_input)
        st.session_state.valor_carta = valor_carta_formatado

        prazo = st.number_input("Prazo (meses)", min_value=1, step=1, value=120)
    with col2:
        fundo_reserva = st.number_input("Fundo de Reserva (%)", min_value=0, step=1, value=3)
        taxa_admin = st.number_input("Taxa de Administração (%)", min_value=0, step=1, value=15)
        taxa_juros_anual = st.number_input("Taxa de Juros Anual da Aplicação (%)", min_value=0.0, step=0.1, value=6.0, format="%.1f")

    st.button("Calcular", use_container_width=True)

    st.markdown("---")
    st.markdown("### 📥 Selecionar itens para PDF")
    
    col_pdf1, col_pdf2, col_pdf3, col_pdf4 = st.columns(4)
    with col_pdf1:
        incluir_sem_lance = st.checkbox("[1] Sem Lance Embutido", value=True, key="incluir_sem_lance")
    with col_pdf2:
        incluir_com_lance = st.checkbox("[2] Com Lance Embutido", value=True, key="incluir_com_lance")
    with col_pdf3:
        incluir_analise_custo = st.checkbox("[3] Análise de Custo", value=True, key="incluir_analise_custo")
    with col_pdf4:
        incluir_analise_vantagem = st.checkbox("[4] Vantagem Financeira", value=True, key="incluir_analise_vantagem")


with col_lance:
    try:
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

    st.markdown(f"### <p style='text-align: center; color: #2c3e50;'>Base de Cálculo (Carta Ajustada): {format_reais(valor_carta_ajustado_com_embutido_preview)}</p>", unsafe_allow_html=True)
    st.caption(f"✨ Valor do crédito desejado: {format_reais(valor_carta_float_preview)}")


limite_embutido = 0.50 if tipo == "Imóvel" else 0.30
erro_embutido = False
if lance_embutido / 100 > limite_embutido:
    st.error(f"🚫 O lance embutido informado ({lance_embutido}%) ultrapassa o limite permitido para {tipo.lower()}. 👉 Para {tipo.lower()}, o máximo permitido é {int(limite_embutido * 100)}%. Corrija o valor para continuar.")
    erro_embutido = True
elif lance_embutido == 100:
    st.error("🚫 O lance embutido não pode ser 100%, pois não haveria valor de carta para ajuste.")
    erro_embutido = True


if not erro_embutido:
    try:
        valor_carta_float = float(st.session_state.valor_carta.replace(".", "").replace(",", "."))
        taxa_total = taxa_admin + fundo_reserva

        # --- CÁLCULOS ---
        total_sem_lance = valor_carta_float * (1 + taxa_total / 100)
        parcela_sem_lance = total_sem_lance / prazo
        valor_lance_padrao = valor_carta_float * (lance_proprio_sem / 100)
        saldo_apos_padrao = total_sem_lance - valor_lance_padrao
        parcela_padrao = saldo_apos_padrao / prazo

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
        diferenca_parcela_pos_contemplacao = parcela_contemplacao_total - parcela_padrao

        taxa_juros_mensal = (1 + taxa_juros_anual / 100)**(1/12) - 1
        saldo_para_aplicar_sem_lance = valor_carta_float - valor_lance_padrao
        rendimento_aplicacao_sem_lance = saldo_para_aplicar_sem_lance * ((1 + taxa_juros_mensal)**prazo)
        ganho_aplicacao_sem_lance = rendimento_aplicacao_sem_lance - saldo_para_aplicar_sem_lance
        encargos_consorcio_sem_lance = valor_carta_float * (taxa_total / 100)
        vantagem_liquida_sem_lance = ganho_aplicacao_sem_lance - encargos_consorcio_sem_lance
        # --- FIM DOS CÁLCULOS ---


        # --- CONSTRUÇÃO DO RESULTADO COM BASE NOS CHECKBOXES ---
        resultado = f"Simulação de Consórcio - {tipo.upper()}\n\n"
        
        # Strings para o PDF, agora sem quebras de linha e com a numeração removida
        pdf_titulo = f"Simulação de Consórcio - {tipo.upper()}"
        
        bloco_sem_lance_pdf = f"""
Valor do crédito: {format_reais(valor_carta_float)}
Parcela mensal (sem contemplação): {format_reais(parcela_sem_lance)}
Parcela com contemplação ({lance_proprio_sem}%): {format_reais(parcela_padrao)}
Valor do lance: {format_reais(valor_lance_padrao)}
Prazo: {prazo} meses
"""
        bloco_com_lance_pdf = f"""
Valor do crédito: {format_reais(valor_carta_float)}
Valor da carta AJUSTADA para Lance Embutido: {format_reais(valor_carta_ajustado_para_embutido)}
Parcela mensal (sem contemplação): {format_reais(parcela_sem_contemplacao_embutido)}
Parcela com contemplação ({lance_proprio_com + lance_embutido}%): {format_reais(parcela_contemplacao_total)}
Lance Próprio: {format_reais(valor_lance_proprio_com_calc)}
Lance Embutido: {format_reais(valor_lance_embutido_com_calc)}
Valor TOTAL do lance: {format_reais(valor_total_lance_calc)}
Prazo: {prazo} meses
"""
        bloco_analise_custo_pdf = f"""
Total de taxas: {taxa_total:.2f}%
Taxa equivalente mensal: {taxa_mensal_total:.2f}%
Taxa equivalente anual: {taxa_anual_total:.2f}%
Diferença entre parcelas pós-contemplação - (Com Lance Embutido - Sem Lance): {format_reais(diferenca_parcela_pos_contemplacao)}
"""
        bloco_analise_vantagem_pdf = f"""
    Cenário Sem Lance Embutido:
        Valor para aplicar: {format_reais(saldo_para_aplicar_sem_lance)} (Montante: {format_reais(saldo_para_aplicar_sem_lance + ganho_aplicacao_sem_lance)})
        Rendimento da aplicação: {format_reais(ganho_aplicacao_sem_lance)}
        Vantagem líquida: {format_reais(vantagem_liquida_sem_lance)}

Observação: Este item ilustra a estratégia de 'não descapitalização'. Ao invés de usar o valor total à vista, o cliente utiliza parte do recurso para dar o lance, e o restante é aplicado em um investimento de renda fixa. A análise compara o rendimento dessa aplicação com os encargos do consórcio, demonstrando a vantagem financeira líquida da operação.
"""

        # Constrói o resultado para a área de texto do Streamlit (mantendo a numeração)
        if incluir_sem_lance:
            resultado += f"""
[1] SEM LANCE EMBUTIDO
{bloco_sem_lance_pdf.strip()}
"""
        if incluir_com_lance:
            resultado += f"""
[2] COM LANCE EMBUTIDO
{bloco_com_lance_pdf.strip()}
"""
        if incluir_analise_custo:
            resultado += f"""
[3] ANÁLISE DE CUSTO
{bloco_analise_custo_pdf.strip()}
"""
        if incluir_analise_vantagem:
            resultado += f"""
[4] ANÁLISE DE VANTAGEM FINANCEIRA COM APLICAÇÃO (Taxa de Juros Anual: {taxa_juros_anual:.2f}%) - Prazo: {prazo} meses
{bloco_analise_vantagem_pdf.strip()}
"""
        
        # --- FIM DA CONSTRUÇÃO DO RESULTADO ---
        
        # Geração do PDF
        buffer = io.BytesIO()
        
        # Estilos para o PDF
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='CustomTitle', fontName='Helvetica-Bold', fontSize=18, spaceAfter=12, alignment=0))
        styles.add(ParagraphStyle(name='CustomSubtitle', fontName='Helvetica', fontSize=12, textColor=(0.33, 0.33, 0.33), spaceAfter=24, alignment=0))
        styles.add(ParagraphStyle(name='CustomHeading', fontName='Helvetica-Bold', fontSize=14, spaceBefore=12, spaceAfter=6, alignment=0))
        styles.add(ParagraphStyle(name='NormalText', fontName='Helvetica', fontSize=10, spaceAfter=6, alignment=0))
        styles.add(ParagraphStyle(name='SmallText', fontName='Helvetica', fontSize=9, spaceAfter=6, alignment=0))

        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
        Story = []

        # Título e Subtítulo
        Story.append(Paragraph(f"📊 {pdf_titulo}", styles['CustomTitle']))
        Story.append(Paragraph("Relatório Gerado pelo Simulador", styles['CustomSubtitle']))

        # Conteúdo baseado na seleção
        if incluir_sem_lance:
            Story.append(Paragraph("SEM LANCE EMBUTIDO", styles['CustomHeading']))
            for line in bloco_sem_lance_pdf.strip().split('\n'):
                Story.append(Paragraph(line, styles['NormalText']))
            Story.append(Spacer(1, 12))

        if incluir_com_lance:
            Story.append(Paragraph("COM LANCE EMBUTIDO", styles['CustomHeading']))
            for line in bloco_com_lance_pdf.strip().split('\n'):
                Story.append(Paragraph(line, styles['NormalText']))
            Story.append(Spacer(1, 12))
        
        if incluir_analise_custo:
            Story.append(Paragraph("ANÁLISE DE CUSTO", styles['CustomHeading']))
            for line in bloco_analise_custo_pdf.strip().split('\n'):
                Story.append(Paragraph(line, styles['NormalText']))
            Story.append(Spacer(1, 12))
        
        if incluir_analise_vantagem:
            Story.append(Paragraph(f"ANÁLISE DE VANTAGEM FINANCEIRA COM APLICAÇÃO (Taxa de Juros Anual: {taxa_juros_anual:.2f}%) - Prazo: {prazo} meses", styles['CustomHeading']))
            # Tratamento especial para a observação
            bloco_vantagem_sem_obs = bloco_analise_vantagem_pdf.split("Observação")[0].strip()
            bloco_obs = "Observação" + bloco_analise_vantagem_pdf.split("Observação")[1]
            
            for line in bloco_vantagem_sem_obs.strip().split('\n'):
                 Story.append(Paragraph(line, styles['NormalText']))

            Story.append(Spacer(1, 6))
            Story.append(Paragraph(bloco_obs, styles['SmallText']))
            Story.append(Spacer(1, 12))
            
        doc.build(Story)
        buffer.seek(0)
        
        st.download_button("📥 Download PDF", buffer, file_name="simulacao_consorcio.pdf", mime="application/pdf")
        st.markdown("### 🧾 Resultado da Simulação")
        st.text_area("Resumo", resultado.strip(), height=800)
    except Exception as e:
        st.error(f"Erro no cálculo: {e}")
