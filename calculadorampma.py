from datetime import date, timedelta, datetime
from io import BytesIO

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ------------------------- CONFIGURAÇÃO BÁSICA ------------------------- #

st.set_page_config(
    page_title="Calculadora de Datas",
    page_icon="🗓️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

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
    """Formata data como 01/01/2025 (quarta-feira)."""
    dia_semana = WEEKDAYS_PT[d.weekday()]
    return f"{d.strftime('%d/%m/%Y')} ({dia_semana})"


# ---------------------- ESTADO (HISTÓRICO / RESULTADO) ----------------- #

if "historico" not in st.session_state:
    st.session_state["historico"] = []

if "ultimo_resultado" not in st.session_state:
    st.session_state["ultimo_resultado"] = ""


def registrar_calculo(
    tipo: str,
    data_inicial: date | None,
    data_final: date | None,
    qtd_dias: int | None,
    resultado_resumido: str,
):
    """Guarda o cálculo no histórico (para a tabela)."""
    st.session_state["historico"].append(
        {
            "Tipo": tipo,
            "Data inicial": data_inicial.strftime("%d/%m/%Y") if data_inicial else "",
            "Data final": data_final.strftime("%d/%m/%Y") if data_final else "",
            "Qtd dias": qtd_dias if qtd_dias is not None else "",
            "Resumo": resultado_resumido,
        }
    )


def botao_copiar(texto: str):
    """Renderiza um botão que copia o resultado para a área de transferência."""
    if not texto:
        return

    # Escapar caracteres problemáticos para o template literal em JS
    safe_text = (
        texto.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("\n", "\\n")
        .replace("\r", "")
    )

    components.html(
        f"""
        <button onclick="navigator.clipboard.writeText(`{safe_text}`)"
                style="
                    margin-top:8px;
                    padding:6px 12px;
                    border-radius:6px;
                    border:none;
                    background-color:#4CAF50;
                    color:white;
                    cursor:pointer;
                ">
            📋 Copiar resultado
        </button>
        """,
        height=60,
    )


def selecionar_data(rotulo: str, data_padrao: date, chave: str) -> date:
    """
    Permite DIGITAR a data no formato dd/mm/aaaa
    e/ou escolher a data num calendário.

    Retorna sempre um objeto date válido.
    """
    col_txt, col_cal = st.columns([3, 2])

    with col_txt:
        texto = st.text_input(
            f"{rotulo} (dd/mm/aaaa)",
            value=data_padrao.strftime("%d/%m/%Y"),
            key=f"{chave}_texto",
        )

    with col_cal:
        data_calendario = st.date_input(
            "Calendário",
            value=data_padrao,
            key=f"{chave}_calendario",
        )

    texto = texto.strip()
    if texto:
        try:
            data_digitada = datetime.strptime(texto, "%d/%m/%Y").date()
            return data_digitada
        except ValueError:
            st.warning(
                f"Data digitada em **{rotulo}** é inválida. "
                "Usando a data selecionada no calendário."
            )
            return data_calendario
    else:
        return data_calendario


# ------------------------------- SIDEBAR -------------------------------- #

with st.sidebar:
    st.title("🗓️ Calculadora")
    st.markdown(
        """
        Escolha o **tipo de cálculo** na tela principal:

        1. Dias entre duas datas  
        2. Data final (inicial + dias)  
        3. Data inicial (final - dias)

        ---
        - Você pode **digitar a data (dd/mm/aaaa)** ou  
          **escolher no calendário**.
        - Use o botão **📋 Copiar resultado** para colar em outro lugar.
        - Abaixo da página há um **histórico** dos cálculos.
        """
    )
    st.caption("Dica: TAB navega entre os campos; ENTER confirma valores.")


# ----------------------------- CABEÇALHO -------------------------------- #

st.markdown(
    """
    <div style="text-align:center; padding: 0.5rem 0;">
        <h1 style="margin-bottom: 0;">🗓️ Calculadora de Datas</h1>
        <p style="color:#555; margin-top: 0.2rem;">
            Digite a data ou escolha no calendário e veja o resultado com dia da semana.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ----------------------------- MENU OPÇÕES ------------------------------ #

st.subheader("⚙️ Escolha o tipo de cálculo")

opcao = st.radio(
    label="Selecione uma opção:",
    options=[
        "1 - Quantidade de dias entre duas datas",
        "2 - Data final (data inicial + quantidade de dias)",
        "3 - Data inicial (data final - quantidade de dias)",
    ],
    index=0,
    help="Clique na opção desejada para exibir os campos correspondentes.",
)

st.divider()

# -------------------------- OPÇÃO 1: DIFERENÇA -------------------------- #
# Permite escolher o tipo de contagem:
# - De data a data (inclui inicial e final)
# - Somente dias completos entre (exclui a data inicial)

if opcao.startswith("1"):
    st.markdown("### 1️⃣ Quantidade de dias entre duas datas")

    modo_contagem = st.radio(
        "Tipo de contagem:",
        options=[
            "De data a data (inclui a data inicial e a data final)",
            "Somente dias completos entre as datas (exclui a data inicial)",
        ],
        index=0,
        help=(
            "Exemplo: 01/01/2025 a 10/01/2025\n"
            "- De data a data = 10 dias\n"
            "- Somente dias completos entre = 9 dias"
        ),
    )

    col1, col2 = st.columns(2)
    with col1:
        data_inicial = selecionar_data(
            "Data inicial", date(2025, 1, 1), "op1_data_inicial"
        )
    with col2:
        data_final = selecionar_data(
            "Data final", date(2025, 1, 10), "op1_data_final"
        )

    st.divider()

    if data_final < data_inicial:
        st.error("⚠️ A data final não pode ser anterior à data inicial.")
    else:
        diferenca_bruta = (data_final - data_inicial).days

        if modo_contagem.startswith("De data a data"):
            qtd_dias = diferenca_bruta + 1
            descricao_modo = "de data a data (incluindo a data inicial e a data final)"
        else:
            qtd_dias = diferenca_bruta
            descricao_modo = "somente dias completos entre as datas (excluindo a data inicial)"

        st.markdown("#### 📊 Resultado")
        st.markdown(f"- **Data inicial:** :blue[{formatar_data(data_inicial)}]")
        st.markdown(f"- **Data final:** :blue[{formatar_data(data_final)}]")
        st.markdown(f"- **Modo de contagem:** `{descricao_modo}`")
        st.success(
            f"📏 Quantidade de dias: **{qtd_dias} dia(s)**"
        )

        resultado_texto = (
            "Cálculo: Diferença entre datas\n"
            f"Modo de contagem: {descricao_modo}\n"
            f"Data inicial: {formatar_data(data_inicial)}\n"
            f"Data final: {formatar_data(data_final)}\n"
            f"Quantidade de dias: {qtd_dias}"
        )
        st.session_state["ultimo_resultado"] = resultado_texto
        botao_copiar(resultado_texto)

        registrar_calculo(
            f"Diferença entre datas ({descricao_modo})",
            data_inicial,
            data_final,
            qtd_dias,
            f"{qtd_dias} dia(s) ({descricao_modo})",
        )

# ------------------------ OPÇÃO 2: DATA FINAL --------------------------- #

elif opcao.startswith("2"):
    st.markdown("### 2️⃣ Data final (data inicial + quantidade de dias)")
    st.caption(
        "Informe a **data inicial** e a **quantidade de dias** a adicionar. "
        "A data final será calculada automaticamente."
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        data_inicial = selecionar_data(
            "Data inicial", date(2025, 1, 1), "op2_data_inicial"
        )
    with col2:
        qtd_dias = st.number_input(
            "➕ Dias a adicionar",
            min_value=0,
            step=1,
            value=9,
            help="Use números inteiros (0, 1, 2, 3...).",
        )

    data_final = data_inicial + timedelta(days=int(qtd_dias))

    st.divider()

    st.markdown("#### 📊 Resultado")
    st.markdown(f"- **Data inicial:** :green[{formatar_data(data_inicial)}]")
    st.markdown(f"- **Dias adicionados:** :green[{int(qtd_dias)}]")
    st.success(f"📅 **Data final:** {formatar_data(data_final)}")

    resultado_texto = (
        "Cálculo: Data final (data inicial + dias)\n"
        f"Data inicial: {formatar_data(data_inicial)}\n"
        f"Dias adicionados: {int(qtd_dias)}\n"
        f"Data final: {formatar_data(data_final)}"
    )
    st.session_state["ultimo_resultado"] = resultado_texto
    botao_copiar(resultado_texto)

    registrar_calculo(
        "Data final (inicial + dias)",
        data_inicial,
        data_final,
        int(qtd_dias),
        f"Final: {data_final.strftime('%d/%m/%Y')}",
    )

# ------------------------ OPÇÃO 3: DATA INICIAL ------------------------- #

else:
    st.markdown("### 3️⃣ Data inicial (data final - quantidade de dias)")
    st.caption(
        "Informe a **data final** e a **quantidade de dias** a subtrair. "
        "A data inicial será calculada automaticamente."
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        data_final = selecionar_data(
            "Data final", date(2025, 1, 10), "op3_data_final"
        )
    with col2:
        qtd_dias = st.number_input(
            "➖ Dias a subtrair",
            min_value=0,
            step=1,
            value=9,
            help="Use números inteiros (0, 1, 2, 3...).",
        )

    data_inicial = data_final - timedelta(days=int(qtd_dias))

    st.divider()

    st.markdown("#### 📊 Resultado")
    st.markdown(f"- **Data final:** :orange[{formatar_data(data_final)}]")
    st.markdown(f"- **Dias subtraídos:** :orange[{int(qtd_dias)}]")
    st.success(f"📅 **Data inicial:** {formatar_data(data_inicial)}")

    resultado_texto = (
        "Cálculo: Data inicial (data final - dias)\n"
        f"Data final: {formatar_data(data_final)}\n"
        f"Dias subtraídos: {int(qtd_dias)}\n"
        f"Data inicial: {formatar_data(data_inicial)}"
    )
    st.session_state["ultimo_resultado"] = resultado_texto
    botao_copiar(resultado_texto)

    registrar_calculo(
        "Data inicial (final - dias)",
        data_inicial,
        data_final,
        int(qtd_dias),
        f"Inicial: {data_inicial.strftime('%d/%m/%Y')}",
    )

# ----------------------------- HISTÓRICO -------------------------------- #

st.divider()
if st.session_state["historico"]:
    st.markdown("### 🧾 Histórico de cálculos")
    st.caption(
        "Os cálculos desta sessão ficam registrados aqui. "
        "Você pode exportar ou limpar o histórico."
    )

    df_hist = pd.DataFrame(st.session_state["historico"])

    col_info, col_limpar = st.columns([3, 1])
    with col_info:
        st.write(f"Total de registros: **{len(df_hist)}**")
    with col_limpar:
        if st.button("🧹 Limpar histórico"):
            st.session_state["historico"] = []
            st.success("Histórico limpo com sucesso!")
            st.stop()

    if st.session_state["historico"]:
        df_hist = pd.DataFrame(st.session_state["historico"])
        st.dataframe(df_hist, use_container_width=True)

        # CSV em memória
        csv_bytes = df_hist.to_csv(index=False).encode("utf-8")

        # Excel em memória
        excel_buffer = BytesIO()
        df_hist.to_excel(excel_buffer, index=False, sheet_name="Histórico")
        excel_buffer.seek(0)

        col_csv, col_xlsx = st.columns(2)
        with col_csv:
            st.download_button(
                label="⬇️ Baixar histórico em CSV",
                data=csv_bytes,
                file_name="historico_calculadora_datas.csv",
                mime="text/csv",
            )
        with col_xlsx:
            st.download_button(
                label="⬇️ Baixar histórico em Excel",
                data=excel_buffer,
                file_name="historico_calculadora_datas.xlsx",
                mime=(
                    "application/vnd.openxmlformats-"
                    "officedocument.spreadsheetml.sheet"
                ),
            )
else:
    st.caption(
        "Nenhum cálculo registrado ainda. "
        "Faça um cálculo para ver o histórico aqui embaixo."
    )
