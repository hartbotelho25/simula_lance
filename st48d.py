import streamlit as st
from streamlit.components.v1 import html as st_components_html
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
import math
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

# Layout compacto: reduz ao máximo o espaço entre blocos
st.markdown("""
    <style>
    section.main .block-container { padding-top: 1rem; padding-bottom: 0.5rem; max-width: 100%; }
    div[data-testid="stVerticalBlock"] > div { padding-top: 0 !important; padding-bottom: 0 !important; }
    div[data-testid="stVerticalBlock"] { gap: 0 !important; }
    div[data-testid="element-container"] { margin-bottom: -0.5rem !important; padding-bottom: 0 !important; }
    .stMarkdown { margin-bottom: 0 !important; margin-top: 0.2rem !important; }
    .stMarkdown h3 { margin-top: 0.4rem !important; margin-bottom: 0.3rem !important; }
    hr { margin: 0.4rem 0 !important; }
    </style>
    """, unsafe_allow_html=True)

# Controle para exibir/ocultar a janela de análise visual da vantagem financeira
if "exibir_lab_vantagem" not in st.session_state:
    st.session_state.exibir_lab_vantagem = False
# Valores únicos: taxa de juros e INPC (alterados no painel principal ou no detalhe)
if "taxa_juros_anual" not in st.session_state:
    st.session_state.taxa_juros_anual = 6.0
if "usar_inpc" not in st.session_state:
    st.session_state.usar_inpc = True
if "fator_inpc_pct" not in st.session_state:
    st.session_state.fator_inpc_pct = 4.5
# Flag: True só quando o slide do detalhe atualizou os canônicos (para não sobrescrever edição do menu principal)
if "sync_from_detail" not in st.session_state:
    st.session_state.sync_from_detail = False
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600&display=swap" rel="stylesheet">
    <div style="font-family: 'Outfit', sans-serif; text-align: center;">
        <p style="font-size: 1.12rem; color: #334155; letter-spacing: 0.12em; font-weight: 600; margin: 0 0 0.6rem 0; text-transform: uppercase;">Desenvolvido por Hart Botelho, CFP®</p>
        <p style="font-size: 0.95rem; color: #64748b; letter-spacing: 0.04em; font-weight: 400; margin: 0;">Feliz 2026 e excelentes negócios!</p>
    </div>
    """, unsafe_allow_html=True)
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

        prazo_maximo = 240 if tipo == "Imóvel" else 100
        prazo = st.number_input("Prazo (meses)", min_value=1, max_value=prazo_maximo, step=1, value=st.session_state.prazo)

        if prazo > prazo_maximo:
            st.info(f"O prazo máximo para {tipo.lower()} é de {prazo_maximo} meses.")
        
        observacoes = st.text_area("Observações Adicionais", height=70)

    with col2:
        # Só copia canônicos para os inputs quando a alteração veio do slide do detalhe (evita “travar” o menu principal)
        if st.session_state.sync_from_detail:
            st.session_state["taxa_juros_anual_input"] = float(st.session_state.taxa_juros_anual)
            st.session_state["usar_inpc_input"] = st.session_state.usar_inpc
            st.session_state["fator_inpc_pct_input"] = float(st.session_state.fator_inpc_pct)
            st.session_state.sync_from_detail = False

        fundo_reserva = st.number_input("Fundo de Reserva (%)", min_value=0.0, step=0.1, value=3.0, format="%.1f")
        taxa_admin = st.number_input("Taxa de Administração (%)", min_value=0.0, step=0.1, value=15.0, format="%.1f")
        st.number_input(
            "Taxa de Juros Anual da Aplicação (%)",
            min_value=0.0, step=0.1, value=float(st.session_state.taxa_juros_anual), format="%.1f", key="taxa_juros_anual_input"
        )
        st.checkbox("Habilitar Fator de Correção INPC", value=st.session_state.usar_inpc, key="usar_inpc_input")
        if st.session_state.usar_inpc_input:
            st.number_input(
                "Fator de correção INPC (%) - média anual",
                min_value=0.0, step=0.1, value=float(st.session_state.fator_inpc_pct), format="%.1f", key="fator_inpc_pct_input"
            )

    # Sincroniza valores do formulário principal com os canônicos (usados em toda a simulação)
    st.session_state.taxa_juros_anual = st.session_state.get("taxa_juros_anual_input", st.session_state.taxa_juros_anual)
    st.session_state.usar_inpc = st.session_state.get("usar_inpc_input", st.session_state.usar_inpc)
    if st.session_state.usar_inpc_input:
        st.session_state.fator_inpc_pct = st.session_state.get("fator_inpc_pct_input", st.session_state.fator_inpc_pct)
    else:
        st.session_state.fator_inpc_pct = 0.0

    taxa_juros_anual = st.session_state.taxa_juros_anual
    usar_inpc = st.session_state.usar_inpc
    fator_inpc_pct = st.session_state.fator_inpc_pct

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

    st.markdown("<div style='margin: 0.2rem 0; border-top: 1px solid #eee;'></div>", unsafe_allow_html=True)
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
            # Força o valor do widget a refletir o lance próprio (R$) do "sem lance" para o "com lance"
            st.session_state["com_lance_proprio"] = percentual_ajustado
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

    st.markdown(f"### <p style='text-align: center; color: #2c3e50; margin: 0.3rem 0;'>Base de Cálculo (Carta Ajustada): {format_reais(valor_carta_ajustado_com_embutido_preview)}</p>", unsafe_allow_html=True)
    st.markdown("<div style='margin: 0.2rem 0; border-top: 1px solid #eee;'></div>", unsafe_allow_html=True)
    st.markdown("### 🏦 Simulação de Financiamento")
    
    col_finan1, col_finan2 = st.columns(2)
    with col_finan1:
        usar_valor_manual = st.checkbox("Insira outro valor", value=False, key="usar_valor_manual")
        
        if usar_valor_manual:
            valor_financiamento_base = st.number_input("Valor do Crédito para simulação (R$)", min_value=0, value=int(valor_carta_float_preview), key="valor_finan_manual")
        else:
            st.markdown(f"**Valor do Crédito:** {format_reais(valor_carta_float_preview)}")
            valor_financiamento_base = valor_carta_float_preview

        prazo_financiamento = st.number_input("Prazo (meses)", min_value=1, step=1, value=prazo, key="prazo_finan")
        
        entrada_financiamento_pct = st.number_input("Entrada (%)", min_value=0, max_value=100, step=1, value=20, key="entrada_financiamento_pct")
    
    with col_finan2:
        taxa_juros_financiamento = st.number_input("Taxa de Juros (% a.a.)", min_value=0.0, step=0.1, value=9.5, format="%.1f", key="taxa_financiamento")
        
        taxa_mensal_financiamento_info = (1 + taxa_juros_financiamento / 100)**(1/12) - 1
        st.markdown(f"**Taxa Equivalente Mensal:** {taxa_mensal_financiamento_info * 100:.2f}%")
        
        cet_acrescimo_default = 1.5 if tipo == "Imóvel" else 3.0
        cet_acrescimo = st.number_input("CET acréscimo (% a.a.)", min_value=1.0, max_value=4.0, step=0.1, value=float(cet_acrescimo_default), format="%.1f", key="cet_acrescimo", help="Acréscimo sobre a taxa nominal para obter o CET. Média imóvel 1,5% a.a. | Veículo 3% a.a.")
        st.caption("Média imóvel 1,5% a.a. | Veículo 3% a.a.")
        cet_aprox_preview = taxa_juros_financiamento + cet_acrescimo
        st.markdown(f"**CET (aprox.):** {cet_aprox_preview:.2f}%")
        
        valor_entrada_financiamento = valor_financiamento_base * (entrada_financiamento_pct / 100)
        valor_principal_financiamento = valor_financiamento_base - valor_entrada_financiamento

    st.markdown(f"""
    <style>
        .compact-text p {{ margin: 0; padding: 0; line-height: 1.2; }}
    </style>
    <div class="compact-text">
        <p>Valor da Entrada (R$): <strong>{format_reais(valor_entrada_financiamento)}</strong></p>
        <p>✨ Valor Financiado: <strong>{format_reais(valor_principal_financiamento)}</strong></p>
    </div>
    """, unsafe_allow_html=True)


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

        # --- CÁLCULOS DO CONSERCIO SEM CORREÇÃO ---
        custo_sem_lance_sem_inpc = valor_carta_float * (taxa_total / 100)
        total_sem_lance = valor_carta_float + custo_sem_lance_sem_inpc
        parcela_sem_lance = total_sem_lance / prazo
        valor_lance_padrao = valor_carta_float * (lance_proprio_sem / 100)
        saldo_apos_padrao = total_sem_lance - valor_lance_padrao
        parcela_padrao = saldo_apos_padrao / prazo
        
        if (1 - (lance_embutido / 100)) > 0:
            valor_carta_ajustado_para_embutido = valor_carta_float / (1 - (lance_embutido / 100))
        else:
            valor_carta_ajustado_para_embutido = valor_carta_float

        custo_com_lance_sem_inpc_fees = valor_carta_ajustado_para_embutido * (taxa_total / 100)
        total_com_lance = valor_carta_ajustado_para_embutido + custo_com_lance_sem_inpc_fees
        parcela_sem_contemplacao_embutido = total_com_lance / prazo
        valor_lance_proprio_com_calc = valor_carta_ajustado_para_embutido * (lance_proprio_com / 100)
        valor_lance_embutido_com_calc = valor_carta_ajustado_com_embutido_preview * (lance_embutido / 100)
        valor_total_lance_calc = valor_lance_proprio_com_calc + valor_lance_embutido_com_calc
        saldo_apos_contemplacao = total_com_lance - valor_total_lance_calc
        parcela_contemplacao_total = saldo_apos_contemplacao / prazo

        # --- PRAZO COM CONTEMPLAÇÃO (amortização no prazo: mesma parcela, menos meses) ---
        if parcela_sem_lance > 0:
            prazo_com_contemplacao_sem = max(1, round(saldo_apos_padrao / parcela_sem_lance))
        else:
            prazo_com_contemplacao_sem = prazo
        if parcela_sem_contemplacao_embutido > 0:
            prazo_com_contemplacao_com = max(1, round(saldo_apos_contemplacao / parcela_sem_contemplacao_embutido))
        else:
            prazo_com_contemplacao_com = prazo

        # --- CUSTO DO CRÉDITO - O TOTAL PAGO PELO CLIENTE (correção) ---
        custo_sem_lance_sem_inpc_total = (parcela_padrao * prazo) + valor_lance_padrao
        # AQUI FOI CORRIGIDO: usa apenas o lance próprio, não o lance total com o embutido
        custo_com_lance_sem_inpc_total = (parcela_contemplacao_total * prazo) + valor_lance_proprio_com_calc

        taxa_mensal_total = taxa_total / prazo
        taxa_anual_total = taxa_mensal_total * 12
        diferenca_parcela_pos_contemplacao = parcela_contemplacao_total - parcela_padrao

        taxa_juros_mensal = (1 + taxa_juros_anual / 100)**(1/12) - 1
        saldo_para_aplicar_sem_lance = valor_carta_float - valor_lance_padrao
        rendimento_aplicacao_sem_lance = saldo_para_aplicar_sem_lance * ((1 + taxa_juros_mensal)**prazo)
        ganho_aplicacao_sem_lance = rendimento_aplicacao_sem_lance - saldo_para_aplicar_sem_lance
        
        encargos_consorcio_sem_lance = custo_sem_lance_sem_inpc_total - valor_carta_float
        vantagem_liquida_sem_lance_original = ganho_aplicacao_sem_lance - encargos_consorcio_sem_lance
        
        custo_sem_lance_inpc_text = ""
        custo_com_lance_inpc_text = ""
        custo_consorcio_corrigido_text = ""
        vantagem_liquida_corrigido_text = ""
        total_inpc_percentual = 0
        inpc_text = ""
        texto_diferenca_amort_prazo = ""  # preenchido quando usar_inpc

        # --- CÁLCULO INPC CORRIGIDO ---
        if usar_inpc and fator_inpc_pct > 0:
            inpc_text = " | Corrigido INPC"
            fator_anual = 1 + fator_inpc_pct / 100
            
            # --- Correção de cálculo do INPC (por ano, menos iterações) ---
            num_anos = (prazo + 11) // 12
            total_acrescimo_sem_lance = 0
            for ano in range(num_anos):
                meses_ano = min(12, prazo - ano * 12)
                total_acrescimo_sem_lance += meses_ano * parcela_padrao * ((fator_anual ** ano) - 1)
            custo_corrigido_sem_lance_total = custo_sem_lance_sem_inpc_total + total_acrescimo_sem_lance
            encargos_consorcio_corrigido = custo_corrigido_sem_lance_total - valor_carta_float

            total_acrescimo_com_lance = 0
            for ano in range(num_anos):
                meses_ano = min(12, prazo - ano * 12)
                total_acrescimo_com_lance += meses_ano * parcela_contemplacao_total * ((fator_anual ** ano) - 1)
            
            custo_corrigido_com_lance_total = custo_com_lance_sem_inpc_total + total_acrescimo_com_lance
            
            
            vantagem_liquida_sem_lance_corrigido = ganho_aplicacao_sem_lance - encargos_consorcio_corrigido
            
            prazo_em_anos = prazo / 12
            total_inpc_percentual = ((1 + fator_inpc_pct / 100)**prazo_em_anos - 1) * 100
            
            custo_sem_lance_inpc_text = f" | Corrigido INPC ({format_reais(custo_corrigido_sem_lance_total)}*)"
            custo_com_lance_inpc_text = f" | Corrigido INPC ({format_reais(custo_corrigido_com_lance_total)}*)"
            
            custo_consorcio_corrigido_text = f" ({format_reais(encargos_consorcio_corrigido)}*)"
            vantagem_liquida_corrigido_text = f" ({format_reais(vantagem_liquida_sem_lance_corrigido)}*)"

            # --- Custo se optar por amortizar o PRAZO (mesma prestação, menos meses) com INPC ---
            num_anos_sem = (prazo_com_contemplacao_sem + 11) // 12
            total_parcelas_amort_prazo_sem = sum(
                min(12, prazo_com_contemplacao_sem - ano * 12) * parcela_sem_lance * (fator_anual ** ano)
                for ano in range(num_anos_sem)
            )
            custo_amort_prazo_sem_corrigido = total_parcelas_amort_prazo_sem + valor_lance_padrao
            diferenca_amort_prazo_sem = custo_amort_prazo_sem_corrigido - custo_corrigido_sem_lance_total

            num_anos_com = (prazo_com_contemplacao_com + 11) // 12
            total_parcelas_amort_prazo_com = sum(
                min(12, prazo_com_contemplacao_com - ano * 12) * parcela_sem_contemplacao_embutido * (fator_anual ** ano)
                for ano in range(num_anos_com)
            )
            custo_amort_prazo_com_corrigido = total_parcelas_amort_prazo_com + valor_lance_proprio_com_calc
            diferenca_amort_prazo_com = custo_amort_prazo_com_corrigido - custo_corrigido_com_lance_total

            sinal_sem = "menor" if diferenca_amort_prazo_sem < 0 else "maior"
            sinal_com = "menor" if diferenca_amort_prazo_com < 0 else "maior"
            texto_diferenca_amort_prazo = (
                f"\n**Se optar por amortizar o prazo** (mesma prestação, menos meses, c/ INPC):\n"
                f"- Sem Lance: {format_reais(custo_amort_prazo_sem_corrigido)} (diferença: {format_reais(abs(diferenca_amort_prazo_sem))} {sinal_sem} que amort. parcela)\n"
                f"- Com Lance: {format_reais(custo_amort_prazo_com_corrigido)} (diferença: {format_reais(abs(diferenca_amort_prazo_com))} {sinal_com} que amort. parcela)\n"
            )

        valor_principal_financiamento = valor_financiamento_base - valor_entrada_financiamento
        taxa_mensal_financiamento = (1 + taxa_juros_financiamento / 100)**(1/12) - 1
        if taxa_mensal_financiamento > 0:
            parcela_financiamento = valor_principal_financiamento * taxa_mensal_financiamento / (1 - (1 + taxa_mensal_financiamento)**-prazo_financiamento)
        else:
            parcela_financiamento = valor_principal_financiamento / prazo_financiamento
        
        custo_total_financiamento = (parcela_financiamento * prazo_financiamento) + valor_entrada_financiamento
        
        cet_anual = taxa_juros_financiamento + cet_acrescimo
        taxa_mensal_cet = (1 + cet_anual / 100)**(1/12) - 1
        if taxa_mensal_cet > 0:
            parcela_financiamento_cet = valor_principal_financiamento * taxa_mensal_cet / (1 - (1 + taxa_mensal_cet)**-prazo_financiamento)
        else:
            parcela_financiamento_cet = valor_principal_financiamento / prazo_financiamento
        custo_total_financiamento_cet = (parcela_financiamento_cet * prazo_financiamento) + valor_entrada_financiamento
        custo_financiamento_cet_text = f" | Corrigido CET ({format_reais(custo_total_financiamento_cet)})"
        
        diferenca_custo_total = custo_total_financiamento - total_sem_lance
        diferenca_parcela_comparativo = parcela_financiamento - parcela_padrao
        

        # --- FIM DOS CÁLCULOS ---

        # Seleção dos blocos que irão para o PDF (próxima do download, layout compacto)
        st.markdown("### 📥 Selecionar itens para PDF")
        col_pdf1, col_pdf2, col_pdf3, col_pdf4, col_pdf5, col_pdf6 = st.columns(6)
        with col_pdf1:
            incluir_sem_lance = st.checkbox("[1] Sem Lance Embutido", value=True, key="incluir_sem_lance")
        with col_pdf2:
            incluir_com_lance = st.checkbox("[2] Com Lance Embutido", value=True, key="incluir_com_lance")
        with col_pdf3:
            incluir_comparativo_financiamento = st.checkbox("[3] Financiamento", value=True, key="incluir_comparativo")
        with col_pdf4:
            incluir_analise_vantagem = st.checkbox("[4] Vantagem Financeira", value=True, key="incluir_analise_vantagem")
            _c1, _c2, _c3 = st.columns([1, 2, 1])
            with _c2:
                if st.button("+ Detalhes", key="abrir_lab_vantagem"):
                    st.session_state.exibir_lab_vantagem = True
        with col_pdf5:
            incluir_analise_custo = st.checkbox("[5] Análise de Custo", value=True, key="incluir_analise_custo")
        with col_pdf6:
            incluir_observacoes = st.checkbox("[6] Observações", value=True, key="incluir_observacoes")

        # CONSTRUÇÃO DINÂMICA DA TABELA DE CUSTO
        bloco_analise_custo_pdf = "**Análise de Custo e Comparativo**\n| Cenário | Custo do crédito |\n|:---|:---:|\n"
        if incluir_sem_lance:
            bloco_analise_custo_pdf += f"| Sem Lance Embutido | {format_reais(custo_sem_lance_sem_inpc_total)}{custo_sem_lance_inpc_text} |\n"
        if incluir_com_lance:
            bloco_analise_custo_pdf += f"| Com Lance Embutido | {format_reais(custo_com_lance_sem_inpc_total)}{custo_com_lance_inpc_text} |\n"
        if usar_inpc and fator_inpc_pct > 0 and (incluir_sem_lance or incluir_com_lance):
            bloco_analise_custo_pdf += "\n**Se optar por amortizar o prazo** (mesma prestação, menos meses, c/ INPC):\n"
            if incluir_sem_lance:
                bloco_analise_custo_pdf += f"- Sem Lance: {format_reais(custo_amort_prazo_sem_corrigido)} (diferença: {format_reais(abs(diferenca_amort_prazo_sem))} {sinal_sem} que amort. parcela)\n"
            if incluir_com_lance:
                bloco_analise_custo_pdf += f"- Com Lance: {format_reais(custo_amort_prazo_com_corrigido)} (diferença: {format_reais(abs(diferenca_amort_prazo_com))} {sinal_com} que amort. parcela)\n"
        if incluir_comparativo_financiamento:
            bloco_analise_custo_pdf += f"\n| Financiamento | {format_reais(custo_total_financiamento)}{custo_financiamento_cet_text} |\n\n"
        if usar_inpc:
             if not incluir_comparativo_financiamento:
                 bloco_analise_custo_pdf += "\n"
             bloco_analise_custo_pdf += f"INPC durante o período: {total_inpc_percentual:.2f}%\n\n"

        bloco_analise_custo_extra_pdf = ""
        
        bloco_sem_lance_pdf = f"""
Cenário: Sem Lance Embutido
Valor do crédito: {format_reais(valor_carta_float)}
Parcela mensal (sem contemplação): {format_reais(parcela_sem_lance)}
▸ Se amortizar parcela ({lance_proprio_sem}%): {format_reais(parcela_padrao)}
Valor do lance: {format_reais(valor_lance_padrao)}
Prazo: {prazo} meses
▸ Se amortizar prazo ({lance_proprio_sem}%): {prazo_com_contemplacao_sem} meses
"""
        lance_total_pct = int(lance_proprio_com) + int(lance_embutido)
        bloco_com_lance_pdf = f"""
Cenário: Com Lance Embutido
Valor do crédito: {format_reais(valor_carta_float)}
Valor da carta AJUSTADA para Lance Embutido: {format_reais(valor_carta_ajustado_para_embutido)}
Parcela mensal (sem contemplação): {format_reais(parcela_sem_contemplacao_embutido)}
▸ Se amortizar parcela ({lance_total_pct}%): {format_reais(parcela_contemplacao_total)}
Lance Próprio ({int(lance_proprio_com)}%): {format_reais(valor_lance_proprio_com_calc)}
Lance Embutido ({int(lance_embutido)}%): {format_reais(valor_lance_embutido_com_calc)}
Valor TOTAL do lance: {format_reais(valor_total_lance_calc)}
Prazo: {prazo} meses
▸ Se amortizar prazo ({lance_total_pct}%): {prazo_com_contemplacao_com} meses
"""
            
        bloco_analise_vantagem_pdf = f"""
    **Cenário Sem Lance Embutido:**
        Valor para aplicar: {format_reais(saldo_para_aplicar_sem_lance)} (Montante: {format_reais(saldo_para_aplicar_sem_lance + ganho_aplicacao_sem_lance)})
        Rendimento da aplicação: {format_reais(ganho_aplicacao_sem_lance)}
        Custo do Consórcio: {format_reais(encargos_consorcio_sem_lance)}{inpc_text}{custo_consorcio_corrigido_text}
        Vantagem líquida: {format_reais(vantagem_liquida_sem_lance_original)}{inpc_text}{vantagem_liquida_corrigido_text}

Observação: Este item ilustra a estratégia de 'não descapitalização'. Ao invés de usar o valor total à vista, o cliente utiliza parte do recurso para dar o lance, e o restante é aplicado em um investimento de renda fixa. A análise compara o rendimento dessa aplicação com os encargos do consórcio, demonstrando a vantagem financeira líquida da operação.
"""
            
        bloco_comparativo_financiamento_pdf = f"""
**Simulação de Financiamento**
    - Valor do Crédito Base: {format_reais(valor_financiamento_base)}
    - Entrada ({entrada_financiamento_pct}%): {format_reais(valor_entrada_financiamento)}
    - Valor Financiado: {format_reais(valor_principal_financiamento)}
    - Parcela Mensal (CET): {format_reais(parcela_financiamento_cet)}
    - Taxa nominal: {taxa_juros_financiamento:.2f}% a.a. | Mensal: {taxa_mensal_financiamento * 100:.2f}%
    - CET anual: {cet_anual:.2f}% | CET mensal: {taxa_mensal_cet * 100:.2f}%
    - Prazo: {prazo_financiamento} meses
    - Total Pago (CET): {format_reais(custo_total_financiamento_cet)}
"""
        
        bloco_observacoes_pdf = f"""
{observacoes}
"""
        
        # --- CONSTRUÇÃO DO RESULTADO COM BASE NOS CHECKBOXES ---
        resultado = f"Simulação de Consórcio - {tipo.upper()}\n\n"
        
        pdf_titulo = f"Simulação de Consórcio - {tipo.upper()}"

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
        styles.add(ParagraphStyle(name='DestaqueText', fontName='Helvetica-Bold', fontSize=10, spaceAfter=6, alignment=0))
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
                elif "Se amortizar" in line or line.strip().startswith("▸"):
                    Story.append(Paragraph(clean_line, styles['DestaqueText']))
                else:
                    Story.append(Paragraph(clean_line, styles['NormalText']))
            Story.append(Spacer(1, 12))

        if incluir_com_lance:
            Story.append(Paragraph("COM LANCE EMBUTIDO", styles['CustomHeading']))
            for line in bloco_com_lance_pdf.strip().split('\n'):
                clean_line = re.sub(r'^Cenário: ', '', line)
                if "Cenário:" in line:
                    Story.append(Paragraph(clean_line, styles['CustomHeading']))
                elif "Se amortizar" in line or line.strip().startswith("▸"):
                    Story.append(Paragraph(clean_line, styles['DestaqueText']))
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

            if bloco_analise_custo_extra_pdf.strip():
                for line in bloco_analise_custo_extra_pdf.strip().split('\n'):
                    Story.append(Paragraph(line, styles['NormalText']))
                Story.append(Spacer(1, 12))

        if incluir_observacoes and observacoes.strip():
            Story.append(Paragraph("OBSERVACÕES ADICIONAIS", styles['CustomHeading']))
            for line in bloco_observacoes_pdf.strip().split('\n'):
                Story.append(Paragraph(line, styles['NormalText']))
            Story.append(Spacer(1, 12))

        doc.build(Story)
        buffer.seek(0)

        st.download_button("📥 Download PDF", buffer, file_name="simulacao_consorcio.pdf", mime="application/pdf")

        st.markdown("### 🧾 Resultado da Simulação")
        st.text_area("Resumo", resultado.strip(), height=420)

        # Janela separada de análise visual, acionada pelo botão na área da Vantagem Financeira
        if st.session_state.get("exibir_lab_vantagem", False) and incluir_analise_vantagem:
            st.markdown(
                "<div id='secao-analise-vantagem' style='margin-top: 1.2rem;'></div>"
                "<script>(function(){ var el = document.getElementById('secao-analise-vantagem'); if (el) setTimeout(function(){ el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 300); })();</script>",
                unsafe_allow_html=True,
            )
            st.markdown("### 🔍 Análise visual da vantagem financeira")
            st.markdown("<p style='font-size: 0.85rem; font-weight: 600; color: #475569; margin-bottom: 0.4rem;'>Lembrete: para proposta sem lance embutido e amortizando a prestação.</p><p style='font-size: 0.8rem; color: #64748b; margin-top: 0; margin-bottom: 1.4rem;'>Altere a taxa de juros ou o INPC abaixo: os valores são replicados automaticamente no painel principal e no resultado da simulação (uma única simulação para o cliente).</p>", unsafe_allow_html=True)

            # Controles sincronizados com o painel principal (alterar aqui atualiza a simulação toda)
            col_ctrl1, col_ctrl2 = st.columns(2)
            with col_ctrl1:
                taxa_juros_anual_lab = st.slider(
                    "Taxa de juros anual da aplicação (%)",
                    min_value=0.0,
                    max_value=20.0,
                    value=float(st.session_state.taxa_juros_anual),
                    step=0.1,
                    key="taxa_juros_anual_lab",
                )
            with col_ctrl2:
                fator_inpc_lab = st.slider(
                    "INPC médio anual (%)",
                    min_value=0.0,
                    max_value=20.0,
                    value=float(st.session_state.fator_inpc_pct) if st.session_state.usar_inpc else 0.0,
                    step=0.1,
                    key="fator_inpc_lab",
                )

            # Replicar no painel principal: ao mudar aqui, atualiza a simulação central e força novo cálculo
            if (taxa_juros_anual_lab != st.session_state.taxa_juros_anual or
                fator_inpc_lab != (st.session_state.fator_inpc_pct if st.session_state.usar_inpc else 0.0)):
                st.session_state.taxa_juros_anual = taxa_juros_anual_lab
                st.session_state.fator_inpc_pct = fator_inpc_lab
                st.session_state.usar_inpc = (fator_inpc_lab > 0)
                st.session_state.sync_from_detail = True  # para o menu principal refletir os valores do slide
                st.rerun()

            # Recalcula apenas a parte da aplicação com a taxa da janela
            taxa_juros_mensal_lab = (1 + taxa_juros_anual_lab / 100)**(1/12) - 1
            rendimento_aplicacao_lab = saldo_para_aplicar_sem_lance * ((1 + taxa_juros_mensal_lab)**prazo)
            ganho_lab = rendimento_aplicacao_lab - saldo_para_aplicar_sem_lance

            # Recalcula o efeito do INPC apenas para esta análise
            encargos_consorcio_corrigido_lab = None
            vantagem_liquida_lab_corrigida = None
            if fator_inpc_lab > 0:
                fator_anual_lab = 1 + fator_inpc_lab / 100
                num_anos_lab = (prazo + 11) // 12
                total_acrescimo_sem_lance_lab = sum(
                    min(12, prazo - ano * 12) * parcela_padrao * ((fator_anual_lab ** ano) - 1)
                    for ano in range(num_anos_lab)
                )
                custo_corrigido_sem_lance_total_lab = custo_sem_lance_sem_inpc_total + total_acrescimo_sem_lance_lab
                encargos_consorcio_corrigido_lab = custo_corrigido_sem_lance_total_lab - valor_carta_float
                vantagem_liquida_lab_corrigida = ganho_lab - encargos_consorcio_corrigido_lab

            # Dados para a narrativa "escolha certa" (apenas neste detalhamento)
            total_prestacoes_mais_lance = custo_corrigido_sem_lance_total_lab if (fator_inpc_lab > 0) else custo_sem_lance_sem_inpc_total
            montante_aplicacao = saldo_para_aplicar_sem_lance + ganho_lab
            desembolso_extra = total_prestacoes_mais_lance - valor_carta_float  # taxa de conveniência (pago ao longo do prazo)
            lucro_real = montante_aplicacao - desembolso_extra  # vantagem real sobre quem comprou à vista
            patrimonio_final_avista = valor_carta_float
            patrimonio_final_consorcio = valor_carta_float + montante_aplicacao
            prazo_anos = prazo / 12
            vantagem_liquida_lab_sem_inpc = ganho_lab - encargos_consorcio_sem_lance

            # Ponto de inversão: primeiro mês em que os juros mensais da aplicação superam a parcela (fórmula fechada)
            mes_inversao = None
            if taxa_juros_mensal_lab > 0 and saldo_para_aplicar_sem_lance > 0 and parcela_padrao > 0:
                denom = saldo_para_aplicar_sem_lance * taxa_juros_mensal_lab
                if denom > 0:
                    if parcela_padrao / denom <= 1:
                        mes_inversao = 1  # juros do 1º mês já superam a parcela
                    else:
                        m_float = math.log(parcela_padrao / denom) / math.log(1 + taxa_juros_mensal_lab)
                        m_int = max(1, math.ceil(m_float))
                        if m_int <= int(prazo):
                            mes_inversao = m_int

            # ----- Patrimônio final comparativo -----
            st.markdown("##### Patrimônio final comparativo")
            col_avista, col_consorcio = st.columns(2)
            with col_avista:
                st.metric("Compra à vista", format_reais(patrimonio_final_avista), help="Apenas o bem")
            with col_consorcio:
                st.metric("Consórcio estruturado", format_reais(patrimonio_final_consorcio), help="Bem + dinheiro no banco")

            # ----- Resumo da aplicação e do consórcio (pares: valor aplicado|prazo, juros|montante, parcelas|vantagem INPC) -----
            total_so_prestacoes = total_prestacoes_mais_lance - valor_lance_padrao
            titulo_prestacoes = "Total das parcelas pagas (com INPC)" if fator_inpc_lab > 0 else "Total das parcelas pagas"
            st.markdown("##### Resumo da aplicação e do consórcio")
            col_valor_apl, col_prazo = st.columns(2)
            with col_valor_apl:
                st.metric("Valor aplicado", format_reais(saldo_para_aplicar_sem_lance))
            with col_prazo:
                st.metric("Prazo do consórcio", f"{int(prazo)} meses", help=f"({prazo/12:.1f} anos)")
            col_juros, col_montante = st.columns(2)
            with col_juros:
                st.metric("Total de juros (aplicação)", format_reais(ganho_lab))
            with col_montante:
                st.metric("Montante do capital", format_reais(montante_aplicacao), help="Valor aplicado + juros")
            col_parcelas, col_vantagem = st.columns(2)
            with col_parcelas:
                st.metric(titulo_prestacoes, format_reais(total_so_prestacoes))
            with col_vantagem:
                if fator_inpc_lab > 0 and vantagem_liquida_lab_corrigida is not None:
                    st.metric("Vantagem líquida (com INPC)", format_reais(vantagem_liquida_lab_corrigida))
                else:
                    st.metric("Vantagem líquida (com INPC)", "—", help="Informe INPC na análise para calcular")

            # ----- Destaque: ponto de inversão -----
            if mes_inversao is not None:
                st.success(
                    f"**A partir do mês {mes_inversao}**, os juros mensais da aplicação passam a superar a parcela: o investimento passa a \"pagar\" o consórcio."
                )

            # Opção de download dos dados da análise em PDF
            buffer_analise = io.BytesIO()
            doc_analise = SimpleDocTemplate(
                buffer_analise,
                pagesize=A4,
                rightMargin=inch,
                leftMargin=inch,
                topMargin=inch,
                bottomMargin=inch,
            )

            StoryAnalise = []
            StoryAnalise.append(Paragraph("📊 Análise de Vantagem Financeira - Detalhes", styles["CustomTitle"]))
            StoryAnalise.append(Spacer(1, 12))

            StoryAnalise.append(Paragraph("Patrimônio final comparativo", styles["CustomHeading"]))
            StoryAnalise.append(Paragraph(f"Compra à vista (apenas o bem): {format_reais(patrimonio_final_avista)}", styles["NormalText"]))
            StoryAnalise.append(Paragraph(f"Consórcio estruturado (bem + dinheiro no banco): {format_reais(patrimonio_final_consorcio)}", styles["NormalText"]))
            StoryAnalise.append(Spacer(1, 6))

            titulo_prestacoes_pdf = "Total das parcelas pagas (com INPC)" if fator_inpc_lab > 0 else "Total das parcelas pagas"
            StoryAnalise.append(Paragraph("Resumo da aplicação e do consórcio", styles["CustomHeading"]))
            StoryAnalise.append(Paragraph(f"Valor aplicado: {format_reais(saldo_para_aplicar_sem_lance)} | Prazo do consórcio: {int(prazo)} meses", styles["NormalText"]))
            StoryAnalise.append(Paragraph(f"Total de juros (aplicação): {format_reais(ganho_lab)} | Montante do capital: {format_reais(montante_aplicacao)}", styles["NormalText"]))
            vantagem_pdf = format_reais(vantagem_liquida_lab_corrigida) if (fator_inpc_lab > 0 and vantagem_liquida_lab_corrigida is not None) else "—"
            StoryAnalise.append(Paragraph(f"{titulo_prestacoes_pdf}: {format_reais(total_so_prestacoes)} | Vantagem líquida (com INPC): {vantagem_pdf}", styles["NormalText"]))
            StoryAnalise.append(Spacer(1, 6))

            if mes_inversao is not None:
                StoryAnalise.append(Paragraph(f"A partir do mês {mes_inversao}, os juros mensais da aplicação superam a parcela: o investimento passa a pagar o consórcio.", styles["NormalText"]))
            StoryAnalise.append(Spacer(1, 6))

            StoryAnalise.append(Paragraph(f"Taxa de juros (análise): {taxa_juros_anual_lab:.2f}% a.a. | INPC (análise): {fator_inpc_lab:.2f}% a.a.", styles["SmallText"]))

            doc_analise.build(StoryAnalise)
            buffer_analise.seek(0)

            st.download_button(
                "📥 Download análise em PDF",
                buffer_analise,
                file_name="analise_vantagem_financeira.pdf",
                mime="application/pdf",
            )
    except Exception as e:
        st.error(f"Erro no cálculo: {e}")
