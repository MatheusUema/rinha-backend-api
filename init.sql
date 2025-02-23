CREATE TABLE IF NOT EXISTS CLIENTE(
    ID_CLIENTE INTEGER NOT NULL,
    NOME_CLIENTE VARCHAR(50) NOT NULL,
    CONSTRAINT PK_CLIENTE PRIMARY KEY (ID_CLIENTE)
);

INSERT INTO CLIENTE (ID_CLIENTE, NOME_CLIENTE) VALUES (1, '100000');


CREATE TABLE IF NOT EXISTS EXTRATO(
    ID_EXTRATO SERIAL NOT NULL,
    SALDO INTEGER NOT NULL,
    DATA_EXTRATO DATE NOT NULL, 
    LIMITE INTEGER NOT NULL,
    CLIENTE  INTEGER NOT NULL,
    CONSTRAINT PK_EXTRATO PRIMARY KEY (ID_EXTRATO),
	CONSTRAINT FK_CLIENTE FOREIGN KEY (CLIENTE) REFERENCES CLIENTE (ID_CLIENTE) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT UQ_EXTRATO_CLIENTE UNIQUE (ID_EXTRATO, CLIENTE),
    CONSTRAINT CHK_EXTRATO CHECK (SALDO + LIMITE >= 0),
	CONSTRAINT CHK_LIMITE CHECK (LIMITE >= 0)
);

CREATE TYPE IF NOT EXISTS TIPO_TRANSACAO AS ENUM ('C', 'D');
CREATE TABLE IF NOT EXISTS TRANSACAO
(
    ID_TRANSACAO SERIAL NOT NULL,
    VALOR INTEGER NOT NULL,
    TIPO TIPO_TRANSACAO NOT NULL,
    DESCRICAO TEXT NOT NULL,
    CLIENTE INTEGER NOT NULL,
    DATA_TRANSACAO TIMESTAMP NOT NULL, 
    CONSTRAINT PK_TRANSACAO PRIMARY KEY (ID_TRANSACAO), 
    CONSTRAINT FK_CLIENTE FOREIGN KEY (CLIENTE) 
        REFERENCES CLIENTE (ID_CLIENTE) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX TRANSACAO_CLIENTE_ID ON TRANSACAO (CLIENTE);
CREATE INDEX TRANSACAO_DATA ON TRANSACAO (DATA_TRANSACAO);

CREATE OR REPLACE PROCEDURE DEBITO(CLIENTE_TRANSACAO INT, SALDO_D INT, DESCRICAO_D TEXT) AS $$
BEGIN
    UPDATE EXTRATO
    SET SALDO_TOTAL = SALDO_TOTAL - SALDO_D
    WHERE CLIENTE = CLIENTE_TRANSACAO;

    INSERT INTO TRANSACAO (CLIENTE, SALDO_TOTAL, TIPO, DATA_TRANSACAO, description)
    VALUES (CLIENTE_TRANSACAO, SALDO_D, 'D', NOW(), DESCRICAO_D);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE PROCEDURE CREDITO(CLIENTE_TRANSACAO INT, SALDO_C INT, DESCRICAO_C TEXT) AS $$
BEGIN
    UPDATE EXTRATO
    SET SALDO_TOTAL = SALDO_TOTAL + SALDO_C
    WHERE CLIENTE = CLIENTE_TRANSACAO;

    INSERT INTO TRANSACAO (CLIENTE, SALDO_TOTAL, TIPO, DATA_TRANSACAO, description)
    VALUES (CLIENTE_TRANSACAO, SALDO_C, 'C', NOW(), DESCRICAO_C);
END;
$$ LANGUAGE plpgsql;