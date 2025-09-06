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
        valor_float = float(float(valor_limpo))
        return f"{int(valor_float):,}".replace(",", ".")
    except ValueError:
        return valor_str

st.set_page_config(page_title="Simulador de Consórcio", layout="wide")
st.markdown("<h6 style='text-align: center; color: gray;'>Desenvolvido por Hart Botelho</h6>", unsafe_allow_html=True)
st.markdown("<h6 style='text-align: center; color: gray; font-size: small;'>Versão 005 | Última atualização em 06/09/2025</h6>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>Simulador de Consórcio</h1>", unsafe_allow_html=True)
st.markdown("### 📋 Informações da Simulação")

col_form, col_lance = st.columns([2, 1])

with col_form:
    if 'tipo_anterior' not in st.session_state:
        st.session_state.tipo_anterior = "Imóvel"
        st.session_state.prazo = 200
        
    tipo = st.selectbox("Tipo de Bem", ["Imóvel", "Veículo"])
    
    if tipo != st.session_state.tipo_anterior:
        if tipo == "Imóvel":
            st.session_state.prazo = 200
        else:
            st.session_state.prazo = 80
        st.session_state.tipo_anterior = tipo
    
    col1, col2 = st.columns(2)
    with col1:
        valor_carta_input = st.text_input("Valor do crédito desejado (R$)", value="100.000", key="valor_carta_raw")
        valor_carta_formatado = format_input_valor(valor_carta_input)
        st.session_state.valor_carta = valor_carta_formatado

        prazo_maximo = 240 if tipo == "Imóvel" else 80
        prazo = st.number_input("Prazo (meses)", min_value=1, max_value=prazo_maximo, step=1, value=st.session_state.prazo)

        if prazo > prazo_maximo:
            st.info(f"O prazo máximo para {tipo.lower()} é de {prazo_maximo} meses.")
        
        observacoes = st.text_area("Observações Adicionais", height=150)

    with col2:
        fundo_reserva = st.number_input("Fundo de Reserva (%)", min_value=0.0, step=0.1, value=3.0, format="%.1f")
        taxa_admin = st.number_input("Taxa de Administração (%)", min_value=0.0, step=0.1, value=15.0, format="%.1f")
        taxa_juros_anual = st.number_input("Taxa de Juros Anual da Aplicação (%)", min_value=0.0, step=0.1, value=6.0, format="%.1f")


    st.markdown("---")
    st.markdown("### 📥 Selecionar itens para PDF")
    
    col_pdf1, col_pdf2, col_pdf3, col_pdf4, col_pdf5, col_pdf6 = st.columns(6)
    with col_pdf1:
        incluir_sem_lance = st.checkbox("[1] Sem Lance Embutido", value=True, key="incluir_sem_lance")
    with col_pdf2:
        incluir_com_lance = st.checkbox("[2] Com Lance Embutido", value=True, key="incluir_com_lance")
    with col_pdf3:
        incluir_comparativo_financiamento = st.checkbox("[3] Financiamento", key="incluir_comparativo")
    with col_pdf4:
        incluir_analise_vantagem = st.checkbox("[4] Vantagem Financeira", value=True, key="incluir_analise_vantagem")
    with col_pdf5:
        incluir_analise_custo = st.checkbox("[5] Análise de Custo", value=True, key="incluir_analise_custo")
    with col_pdf6:
        incluir_observacoes = st.checkbox("[6] Observações", key="incluir_observacoes")
        
with col_lance:
    try:
        valor_carta_float_preview = float(st.session_state.valor_carta.replace(".", "").replace(",", "."))
    except:
        valor_carta_float_preview = 0.0
    
    st.markdown("### 🎯 Sem Lance Embutido")
    col_sem1, col_sem2 = st.columns([1, 1])
    with col_sem1:
        lance_proprio_sem = st.number_input("Lance Próprio (%)", min_value=0, max_value=100, step=1, value=10, key="sem_lance")
        st.session_state.lance_proprio_sem = lance_proprio_sem
    with col_sem2:
        valor_lance_proprio_sem = valor_carta_float_preview * (lance_proprio_sem / 100)
        st.markdown(f"**{format_reais(valor_lance_proprio_sem)}**")

    st.markdown("---")
    
    col_titulo_com_lance, col_trava_lance = st.columns([2, 1])
    with col_titulo_com_lance:
        st.markdown("### 🎯 Com Lance Embutido")
    with col_trava_lance:
        replicar_lance = st.checkbox("Usar mesmo valor de Lance Próprio (R$)", value=False, key="replicar_lance")

    col_com1, col_com2 = st.columns([1, 1])

    with col_com1:
        if replicar_lance:
            if (1 - (st.session_state.com_lance_embutido / 100)) > 0:
                valor_carta_ajustado_com_embutido = valor_carta_float_preview / (1 - (st.session_state.com_lance_embutido / 100))
            else:
                valor_carta_ajustado_com_embutido = valor_carta_float_preview
            
            valor_em_reais_do_sem_lance = valor_carta_float_preview * (st.session_state.lance_proprio_sem / 100)
            
            if valor_carta_ajustado_com_embutido > 0:
                percentual_ajustado = (valor_em_reais_do_sem_lance / valor_carta_ajustado_com_embutido) * 100
            else:
                percentual_ajustado = 0
            
            lance_proprio_com = st.number_input("Lance Próprio (%)", min_value=0.0, max_value=100.0, step=0.1, value=percentual_ajustado, disabled=True, format="%.2f", key="com_lance_proprio")
        else:
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
    
    # NOVOS CAMPOS PARA SIMULAÇÃO DE FINANCIAMENTO
    st.markdown("---")
    st.markdown("### 🏦 Simulação de Financiamento")
    
    col_finan1, col_finan2 = st.columns(2)
    with col_finan1:
        # Checkbox para habilitar o valor manual
        usar_valor_manual = st.checkbox("Usar valor de crédito manual", value=False, key="usar_valor_manual")
        
        # Campo de input condicional
        if usar_valor_manual:
            valor_financiamento_base = st.number_input("Valor do Crédito para simulação (R$)", min_value=0, value=int(valor_carta_float_preview), key="valor_finan_manual")
        else:
            st.markdown(f"**Valor do Crédito:** {format_reais(valor_carta_float_preview)}")
            valor_financiamento_base = valor_carta_float_preview

        prazo_financiamento = st.number_input("Prazo (meses)", min_value=1, step=1, value=prazo, key="prazo_finan")
    
    with col_finan2:
        taxa_juros_financiamento = st.number_input("Taxa de Juros (% a.a.)", min_value=0.0, step=0.1, value=9.5, format="%.1f", key="taxa_financiamento")
        entrada_financiamento_pct = st.number_input("Entrada (%)", min_value=0, max_value=100, step=1, value=20, key="entrada_financiamento_pct")
        
        valor_entrada_financiamento = valor_financiamento_base * (entrada_financiamento_pct / 100)
        st.markdown("Valor da Entrada (R$)")
        st.markdown(f"**{format_reais(valor_entrada_financiamento)}**")
        
        valor_principal_financiamento = valor_financiamento_base - valor_entrada_financiamento
        st.markdown(f"✨ **Valor Financiado:** {format_reais(valor_principal_financiamento)}")


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
        
        custo_adicional_total_taxas = (valor_carta_ajustado_para_embutido * (taxa_total / 100)) - (valor_carta_float * (taxa_total / 100))
        custo_adicional_mensal_taxas = custo_adicional_total_taxas / prazo

        percentual_embutido_sobre_credito = (valor_lance_embutido_com_calc / valor_carta_float) * 100

        # Novos cálculos
        taxa_mensal_financiamento = (taxa_juros_financiamento / 100) / 12
        if taxa_mensal_financiamento > 0:
            parcela_financiamento = valor_principal_financiamento * taxa_mensal_financiamento / (1 - (1 + taxa_mensal_financiamento)**-prazo_financiamento)
        else:
            parcela_financiamento = valor_principal_financiamento / prazo_financiamento
        
        custo_total_financiamento = (parcela_financiamento * prazo_financiamento) + valor_entrada_financiamento
        
        diferenca_custo_total = custo_total_financiamento - total_sem_lance
        diferenca_parcela_comparativo = parcela_financiamento - parcela_padrao

        # --- FIM DOS CÁLCULOS ---


        # --- CONSTRUÇÃO DO RESULTADO COM BASE NOS CHECKBOXES ---
        resultado = f"Simulação de Consórcio - {tipo.upper()}\n\n"
        
        pdf_titulo = f"Simulação de Consórcio - {tipo.upper()}"
        
        bloco_sem_lance_pdf = f"""
Cenário: Sem Lance Embutido
Valor do crédito: {format_reais(valor_carta_float)}
Parcela mensal (sem contemplação): {format_reais(parcela_sem_lance)}
Parcela com contemplação ({lance_proprio_sem}%): {format_reais(parcela_padrao)}
Valor do lance: {format_reais(valor_lance_padrao)}
Prazo: {prazo} meses
"""
        bloco_com_lance_pdf = f"""
Cenário: Com Lance Embutido
Valor do crédito: {format_reais(valor_carta_float)}
Valor da carta AJUSTADA para Lance Embutido: {format_reais(valor_carta_ajustado_para_embutido)}
Parcela mensal (sem contemplação): {format_reais(parcela_sem_contemplacao_embutido)}
Parcela com contemplação ({int(lance_proprio_com) + int(lance_embutido)}%): {format_reais(parcela_contemplacao_total)}
Lance Próprio ({int(lance_proprio_com)}%): {format_reais(valor_lance_proprio_com_calc)}
Lance Embutido ({int(lance_embutido)}%): {format_reais(valor_lance_embutido_com_calc)}
Valor TOTAL do lance: {format_reais(valor_total_lance_calc)}
Prazo: {prazo} meses
"""
        bloco_analise_custo_pdf = f"""
**Análise de Custo e Comparativo**
| Cenário | Custo Total do Plano |
|:---|:---:|
| Sem Lance Embutido | {format_reais(total_sem_lance)} |
| Com Lance Embutido | {format_reais(total_corrigido)} |
| Financiamento | {format_reais(custo_total_financiamento)} |
"""
        bloco_analise_custo_extra_pdf = f"""
Total de taxas: {taxa_total:.2f}%
Taxa equivalente mensal: {taxa_mensal_total:.2f}%
Taxa equivalente anual: {taxa_anual_total:.2f}%
Diferença entre parcelas pós-contemplação - (Com Lance Embutido - Sem Lance): {format_reais(diferenca_parcela_pos_contemplacao)}
"""

        bloco_analise_vantagem_pdf = f"""
    **Cenário Sem Lance Embutido:**
        Valor para aplicar: {format_reais(saldo_para_aplicar_sem_lance)} (Montante: {format_reais(saldo_para_aplicar_sem_lance + ganho_aplicacao_sem_lance)})
        Rendimento da aplicação: {format_reais(ganho_aplicacao_sem_lance)}
        Custo do Consórcio: {format_reais(encargos_consorcio_sem_lance)}
        Vantagem líquida: {format_reais(vantagem_liquida_sem_lance)}

Observação: Este item ilustra a estratégia de 'não descapitalização'. Ao invés de usar o valor total à vista, o cliente utiliza parte do recurso para dar o lance, e o restante é aplicado em um investimento de renda fixa. A análise compara o rendimento dessa aplicação com os encargos do consórcio, demonstrando a vantagem financeira líquida da operação.
"""
        bloco_comparativo_financiamento_pdf = f"""
**Simulação de Financiamento**
    - Valor do Crédito Base: {format_reais(valor_financiamento_base)}
    - Entrada ({entrada_financiamento_pct}%): {format_reais(valor_entrada_financiamento)}
    - Valor Financiado: {format_reais(valor_principal_financiamento)}
    - Parcela Mensal: {format_reais(parcela_financiamento)}
    - Prazo: {prazo_financiamento} meses
    - Taxa de Juros Anual: {taxa_juros_financiamento:.2f}%
    - Total Pago: {format_reais(custo_total_financiamento)}
"""
        
        bloco_observacoes_pdf = f"""
{observacoes}
"""

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
        if incluir_comparativo_financiamento:
            resultado += f"""
[3] FINANCIAMENTO
{bloco_comparativo_financiamento_pdf.strip()}
"""
        if incluir_analise_vantagem:
            resultado += f"""
[4] ANÁLISE DE VANTAGEM FINANCEIRA COM APLICAÇÃO (Taxa de Juros Anual: {taxa_juros_anual:.2f}%) - Prazo: {prazo} meses
{bloco_analise_vantagem_pdf.strip()}
"""
        if incluir_analise_custo:
            resultado += f"""
[5] ANÁLISE DE CUSTO
{bloco_analise_custo_pdf.strip()}

{bloco_analise_custo_extra_pdf.strip()}
"""
        if incluir_observacoes and observacoes.strip():
            resultado += f"""
[6] OBSERVAÇÕES ADICIONAIS
{bloco_observacoes_pdf.strip()}
"""
        
        buffer = io.BytesIO()
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='CustomTitle', fontName='Helvetica-Bold', fontSize=18, spaceAfter=12, alignment=0))
        styles.add(ParagraphStyle(name='CustomSubtitle', fontName='Helvetica', fontSize=12, textColor=(0.33, 0.33, 0.33), spaceAfter=24, alignment=0))
        styles.add(ParagraphStyle(name='CustomHeading', fontName='Helvetica-Bold', fontSize=14, spaceBefore=12, spaceAfter=6, alignment=0))
        styles.add(ParagraphStyle(name='NormalText', fontName='Helvetica', fontSize=10, spaceAfter=6, alignment=0))
        styles.add(ParagraphStyle(name='SmallText', fontName='Helvetica', fontSize=9, spaceAfter=6, alignment=0))

        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
        Story = []

        Story.append(Paragraph(f"📊 {pdf_titulo}", styles['CustomTitle']))
        Story.append(Paragraph("Relatório Gerado pelo Simulador", styles['CustomSubtitle']))

        if incluir_sem_lance:
            Story.append(Paragraph("SEM LANCE EMBUTIDO", styles['CustomHeading']))
            for line in bloco_sem_lance_pdf.strip().split('\n'):
                clean_line = re.sub(r'^Cenário: ', '', line)
                if "Cenário:" in line:
                    Story.append(Paragraph(clean_line, styles['CustomHeading']))
                else:
                    Story.append(Paragraph(clean_line, styles['NormalText']))
            Story.append(Spacer(1, 12))

        if incluir_com_lance:
            Story.append(Paragraph("COM LANCE EMBUTIDO", styles['CustomHeading']))
            for line in bloco_com_lance_pdf.strip().split('\n'):
                clean_line = re.sub(r'^Cenário: ', '', line)
                if "Cenário:" in line:
                    Story.append(Paragraph(clean_line, styles['CustomHeading']))
                else:
                    Story.append(Paragraph(clean_line, styles['NormalText']))
            Story.append(Spacer(1, 12))
        
        if incluir_comparativo_financiamento:
            Story.append(Paragraph("FINANCIAMENTO", styles['CustomHeading']))
            comparativo_lines = bloco_comparativo_financiamento_pdf.strip().split('\n')
            for line in comparativo_lines:
                if "|" in line:
                    Story.append(Paragraph(line.replace("|", " | "), styles['NormalText']))
                else:
                    Story.append(Paragraph(line, styles['NormalText']))
            Story.append(Spacer(1, 12))

        if incluir_analise_vantagem:
            Story.append(Paragraph(f"ANÁLISE DE VANTAGEM FINANCEIRA COM APLICAÇÃO (Taxa de Juros Anual: {taxa_juros_anual:.2f}%) - Prazo: {prazo} meses", styles['CustomHeading']))
            
            bloco_vantagem_sem_obs = bloco_analise_vantagem_pdf.split("Observação")[0].strip()
            bloco_vantagem_sem_obs_limpo = bloco_vantagem_sem_obs.replace("**", "") 
            bloco_obs = "Observação" + bloco_analise_vantagem_pdf.split("Observação")[1]
            
            for line in bloco_vantagem_sem_obs_limpo.strip().split('\n'):
                 Story.append(Paragraph(line, styles['NormalText']))

            Story.append(Spacer(1, 6))
            Story.append(Paragraph(bloco_obs, styles['SmallText']))
            Story.append(Spacer(1, 12))

        if incluir_analise_custo:
            Story.append(Paragraph("ANÁLISE DE CUSTO", styles['CustomHeading']))
            
            table_lines = bloco_analise_custo_pdf.strip().split('\n')
            for line in table_lines:
                Story.append(Paragraph(line.replace("|", " | "), styles['NormalText']))
            
            Story.append(Spacer(1, 12))

            for line in bloco_analise_custo_extra_pdf.strip().split('\n'):
                Story.append(Paragraph(line, styles['NormalText']))
            Story.append(Spacer(1, 12))

        if incluir_observacoes and observacoes.strip():
            Story.append(Paragraph("OBSERVAÇÕES ADICIONAIS", styles['CustomHeading']))
            for line in bloco_observacoes_pdf.strip().split('\n'):
                Story.append(Paragraph(line, styles['NormalText']))
            Story.append(Spacer(1, 12))

        doc.build(Story)
        buffer.seek(0)
        
        st.download_button("📥 Download PDF", buffer, file_name="simulacao_consorcio.pdf", mime="application/pdf")
        st.markdown("### 🧾 Resultado da Simulação")
        st.text_area("Resumo", resultado.strip(), height=800)
    except Exception as e:
        st.error(f"Erro no cálculo: {e}")
