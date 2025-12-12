from datetime import date, timedelta, datetime
from io import BytesIO

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ------------------------- CONFIGURAÇÃO BÁSICA ------------------------- #

st.set_page_config(
    page_title="Calculadora de Datas da Vovó",
    page_icon="🗓️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ------------------------------ ESTILO CSS ----------------------------- #

CUSTOM_CSS = """
<style>
body {
    background-color: #f3f4f6;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0f172a !important;
}

/* Reduzindo espaço vertical geral */
.block-container {
    padding-top: 0.6rem !important;
    padding-bottom: 1.2rem !important;
    max-width: 900px !important;
}

/* Título mais compacto */
h2 {
    color: #111827;
    font-weight: 700;
    margin-bottom: 0.1rem !important;
}

/* Subtítulo mais compacto */
p.subtitle {
    color: #4b5563;
    margin-top: 0.1rem !important;
    margin-bottom: 0.6rem !important;
}

/* Divisor mais fino logo após o título */
.thin-divider {
    height: 6px;
    margin: 0.2rem 0 0.6rem 0;
    border-bottom: 1px solid #d1d5db;
}

/* Cards de formulário */
div[data-testid="stForm"] {
    padding: 1rem 1.2rem;
    border-radius: 14px;
    background-color: #ffffff;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
    border: 1px solid #e5e7eb;
}

/* Botões principais */
.stButton > button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: white;
    border-radius: 999px;
    border: none;
    padding: 0.45rem 1.4rem;
    font-weight: 600;
    font-size: 0.9rem;
    cursor: pointer;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #1d4ed8, #1e40af);
}

/* Botões secundários (limpar histórico, etc.) */
button[kind="secondary"] {
    border-radius: 999px !important;
}

/* Radios mais agradáveis */
div[role="radiogroup"] > label {
    padding: 0.25rem 0.1rem;
}

/* Inputs de data */
input[data-adriano="data"] {
    border-radius: 10px;
    border: 1px solid #d1d5db;
    padding: 0.35rem 0.5rem;
}

/* Inputs numéricos */
input[type="number"] {
    border-radius: 10px;
}

/* Tabela do histórico */
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
}

/* Alertas */
.stAlert {
    border-radius: 10px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --------------------------- CONSTANTES -------------------------------- #

WEEKDAYS_PT = [
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
]


def formatar_data(d: date) -> str:
    dia_semana = WEEKDAYS_PT[d.weekday()]
    return f"{d.strftime('%d/%m/%Y')} ({dia_semana})"


# ---------------------- ESTADO (HISTÓRICO / RESULTADO) ----------------- #

if "historico" not in st.session_state:
    st.session_state["historico"] = []

if "ultimo_resultado" not in st.session_state:
    st.session_state["ultimo_resultado"] = ""


def registrar_calculo(tipo, data_inicial, data_final, qtd_dias, resumo):
    st.session_state["historico"].append(
        {
            "Tipo": tipo,
            "Data inicial": data_inicial.strftime("%d/%m/%Y") if data_inicial else "",
            "Data final": data_final.strftime("%d/%m/%Y") if data_final else "",
            "Qtd dias": qtd_dias,
            "Resumo": resumo,
        }
    )


def botao_copiar(texto: str):
    if not texto:
        return

    safe_text = (
        texto.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("\n", "\\n")
    )

    components.html(
        f"""
        <button onclick="navigator.clipboard.writeText(`{safe_text}`)"
                style="
                    margin-top:8px;
                    padding:6px 12px;
                    border-radius:999px;
                    border:none;
                    background:linear-gradient(135deg,#16a34a,#15803d);
                    color:white;
                    cursor:pointer;
                    font-weight:600;
                ">
            📋 Copiar resultado
        </button>
        """,
        height=60,
    )


# --------- Período em anos, meses e dias (para mostrar entre parênteses) ------- #

def periodo_anos_meses_dias(data_inicial: date, data_final: date, inclusivo: bool) -> str:
    if inclusivo:
        data_final_calc = data_final + timedelta(days=1)
    else:
        data_final_calc = data_final

    try:
        from dateutil.relativedelta import relativedelta
        rd = relativedelta(data_final_calc, data_inicial)
        anos, meses, dias = rd.years, rd.months, rd.days
    except ModuleNotFoundError:
        total_dias = (data_final_calc - data_inicial).days
        anos = total_dias // 365
        resto = total_dias % 365
        meses = resto // 30
        dias = resto % 30

    partes = []
    if anos:
        partes.append(f"{anos} ano{'s' if anos != 1 else ''}")
    if meses:
        partes.append(f"{meses} mês{'es' if meses != 1 else ''}")
    if dias or not partes:
        partes.append(f"{dias} dia{'s' if dias != 1 else ''}")

    return " (" + ", ".join(partes) + ")"


# ---------------- CAMPO DE DATA COM MÁSCARA (RETORNA STRING) ----------- #

def selecionar_data(rotulo: str, valor_padrao: str, chave: str) -> str:
    """
    Campo de texto com máscara automática dd/mm/aaaa.
    Retorna a STRING digitada. A validação é feita depois do botão CALCULAR.
    """
    texto = st.text_input(
        f"{rotulo} (dd/mm/aaaa)",
        value=valor_padrao,
        key=chave,
        placeholder="dd/mm/aaaa",
        label_visibility="visible",
    )

    # Máscara associada a ESTE campo
    components.html(
        f"""
        <script>
        (function() {{
            const frame = window.frameElement;
            if (!frame) return;
            const doc = frame.ownerDocument;
            const inputs = doc.querySelectorAll('input[id="{chave}"]');
            if (!inputs.length) return;
            const campo = inputs[0];
            campo.setAttribute('data-adriano', 'data');
            if (campo.dataset.masked === "true") return;
            campo.dataset.masked = "true";

            campo.addEventListener('input', function() {{
                let v = campo.value.replace(/\\D/g, "").slice(0, 8);
                let f = "";
                if (v.length <= 2) {{
                    f = v;
                }} else if (v.length <= 4) {{
                    f = v.slice(0,2) + "/" + v.slice(2);
                }} else {{
                    f = v.slice(0,2) + "/" + v.slice(2,4) + "/" + v.slice(4);
                }}
                campo.value = f;
            }});
        }})();
        </script>
        """,
        height=0,
        width=0,
    )

    return texto.strip()


def tentar_converter_data(texto: str, nome_campo: str, chave_state: str) -> date | None:
    """
    Tenta converter a string em date.
    Se der erro:
      - mostra mensagem;
      - limpa o campo (session_state[chave_state] = "");
      - retorna None.
    """
    if not texto:
        st.error(f"O campo **{nome_campo}** não pode ficar em branco.")
        return None

    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        st.error(f"Data inválida no campo **{nome_campo}** — digite no formato dd/mm/aaaa.")
        st.session_state[chave_state] = ""
        return None


# ------------------------------- SIDEBAR -------------------------------- #

with st.sidebar:
    st.title("🗓️ Calculadora de Datas")
    st.markdown(
        """
        ➤ Digite sempre no formato **dd/mm/aaaa**  

        **Tipos de cálculo**
        1. Diferença entre datas  
        2. Data final (início + dias)  
        3. Data inicial (final - dias)  

        **Extras**
        - Botão **Copiar resultado**
        - **Histórico** com exportação CSV/Excel
        - Botão **Limpar histórico**
        """
    )

# ----------------------------- CABEÇALHO -------------------------------- #

st.markdown(
    """
    <div style="text-align:center;">
        <h2>🗓️ Calculadora de Datas</h2>
        <p class="subtitle">
            Digite as datas, escolha o tipo de cálculo e clique em <b>CALCULAR</b>.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# divisor compacto
st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)

# ----------------------------- MENU OPÇÕES ------------------------------ #

opcao = st.radio(
    "Selecione o tipo de cálculo:",
    [
        "1 - Quantidade de dias entre duas datas",
        "2 - Data final (data inicial + quantidade de dias)",
        "3 - Data inicial (data final - quantidade de dias)",
    ]
)

st.divider()

# ======================================================================
#                         OPÇÃO 1 – DIFERENÇA DE DATAS
# ======================================================================

if opcao.startswith("1"):

    st.subheader("Diferença entre datas")

    with st.form("form_op1"):
        modo = st.radio(
            "Modo de contagem:",
            [
                "De data a data (inclui data inicial e final)",
                "Somente dias completos entre as datas",
            ]
        )

        col1, col2 = st.columns(2)
        with col1:
            txt_inicial = selecionar_data("Data inicial", "", "data_inicial_op1")
        with col2:
            txt_final = selecionar_data("Data final", "", "data_final_op1")

        calcular = st.form_submit_button("🔵 CALCULAR")

    if calcular:
        data_inicial = tentar_converter_data(txt_inicial, "Data inicial", "data_inicial_op1")
        data_final = tentar_converter_data(txt_final, "Data final", "data_final_op1")

        if (data_inicial is not None) and (data_final is not None):
            if data_final < data_inicial:
                st.error("A data final não pode ser anterior à inicial.")
            else:
                dias_bruto = (data_final - data_inicial).days

                if modo.startswith("De data a data"):
                    dias = dias_bruto + 1
                    descricao = "Contagem de data a data (inclui a data inicial e a final)"
                    inclusivo = True
                else:
                    dias = dias_bruto
                    descricao = "Somente dias completos entre as datas"
                    inclusivo = False

                periodo_str = periodo_anos_meses_dias(data_inicial, data_final, inclusivo)

                st.success(f"Total: **{dias} dia(s)**{periodo_str}")
                st.write(f"- **Data inicial:** {formatar_data(data_inicial)}")
                st.write(f"- **Data final:** {formatar_data(data_final)}")
                st.write(f"- **Modo:** {descricao}")

                resultado = (
                    f"Cálculo de diferença entre datas\n"
                    f"{descricao}\n"
                    f"Data inicial: {formatar_data(data_inicial)}\n"
                    f"Data final: {formatar_data(data_final)}\n"
                    f"Total de dias: {dias}{periodo_str}"
                )

                botao_copiar(resultado)
                registrar_calculo("Diferença entre datas", data_inicial, data_final, dias, descricao)

# ======================================================================
#                     OPÇÃO 2 – DATA FINAL
# ======================================================================

elif opcao.startswith("2"):

    st.subheader("Data final (data inicial + dias)")

    with st.form("form_op2"):
        col1, col2 = st.columns(2)
        with col1:
            txt_inicial = selecionar_data("Data inicial", "", "data_inicial_op2")
        with col2:
            qtd = st.number_input("Dias a adicionar:", min_value=0, value=0, step=1)

        calcular = st.form_submit_button("🔵 CALCULAR")

    if calcular:
        data_inicial = tentar_converter_data(txt_inicial, "Data inicial", "data_inicial_op2")

        if data_inicial is not None:
            data_final = data_inicial + timedelta(days=int(qtd))
            periodo_str = periodo_anos_meses_dias(data_inicial, data_final, inclusivo=False)

            st.success(f"Data final: **{formatar_data(data_final)}**")
            st.write(f"- Dias adicionados: {int(qtd)}{periodo_str}")
            st.write(f"- Data inicial: {formatar_data(data_inicial)}")

            resultado = (
                f"Data final (início + dias)\n"
                f"Data inicial: {formatar_data(data_inicial)}\n"
                f"Dias adicionados: {int(qtd)}{periodo_str}\n"
                f"Data final: {formatar_data(data_final)}"
            )

            botao_copiar(resultado)
            registrar_calculo("Data final (início + dias)", data_inicial, data_final, int(qtd), "Somatório")

# ======================================================================
#                     OPÇÃO 3 – DATA INICIAL
# ======================================================================

else:

    st.subheader("Data inicial (data final - dias)")

    with st.form("form_op3"):
        col1, col2 = st.columns(2)
        with col1:
            txt_final = selecionar_data("Data final", "", "data_final_op3")
        with col2:
            qtd = st.number_input("Dias a subtrair:", min_value=0, value=0, step=1)

        calcular = st.form_submit_button("🔵 CALCULAR")

    if calcular:
        data_final = tentar_converter_data(txt_final, "Data final", "data_final_op3")

        if data_final is not None:
            data_inicial = data_final - timedelta(days=int(qtd))
            periodo_str = periodo_anos_meses_dias(data_inicial, data_final, inclusivo=False)

            st.success(f"Data inicial: **{formatar_data(data_inicial)}**")
            st.write(f"- Dias subtraídos: {int(qtd)}{periodo_str}")
            st.write(f"- Data final: {formatar_data(data_final)}")

            resultado = (
                f"Data inicial (final - dias)\n"
                f"Data final: {formatar_data(data_final)}\n"
                f"Dias subtraídos: {int(qtd)}{periodo_str}\n"
                f"Data inicial: {formatar_data(data_inicial)}"
            )

            botao_copiar(resultado)
            registrar_calculo("Data inicial (final - dias)", data_inicial, data_final, int(qtd), "Subtração")

# ======================================================================
#                          HISTÓRICO
# ======================================================================

st.divider()
st.subheader("📜 Histórico")

if st.session_state["historico"]:
    df = pd.DataFrame(st.session_state["historico"])
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "⬇️ Baixar CSV",
            csv,
            "historico_calculadora_datas.csv",
            mime="text/csv",
        )

    with col2:
        try:
            excel = BytesIO()
            df.to_excel(excel, index=False, sheet_name="Histórico")
            excel.seek(0)
            st.download_button(
                "⬇️ Baixar Excel",
                excel,
                "historico_calculadora_datas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except ModuleNotFoundError:
            st.warning(
                "Para exportar em Excel (.xlsx), instale o pacote **openpyxl** "
                "no ambiente (requirements.txt)."
            )

    with col3:
        if st.button("🧹 Limpar histórico"):
            st.session_state["historico"] = []
            st.success("Histórico limpo!")
else:
    st.info("Nenhum cálculo registrado.")
