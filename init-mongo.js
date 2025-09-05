// Script de inicialização do MongoDB
db = db.getSiblingDB('rpg_textual');

// Criar usuário para a aplicação
db.createUser({
    user: 'rpg_user',
    pwd: 'rpg_password123',
    roles: [
        {
            role: 'readWrite',
            db: 'rpg_textual'
        }
    ]
});

print('Base de dados inicializada com sucesso!');