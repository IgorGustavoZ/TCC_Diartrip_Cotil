// Global fetch interceptor: injects CSRF token header and handles 401 redirects.
;(function () {
    const _orig = window.fetch.bind(window)
    const _MUTANTES = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

    function _getCsrfToken() {
        const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/)
        return match ? decodeURIComponent(match[1]) : null
    }

    window.fetch = async function (...args) {
        let resource = args[0]
        let config = args[1] ? { ...args[1] } : {}
        const method = (config.method || 'GET').toUpperCase()

        if (_MUTANTES.has(method)) {
            const token = _getCsrfToken()
            if (token) {
                config.headers = { ...(config.headers || {}), 'X-CSRF-Token': token }
            }
        }

        const resp = await _orig(resource, config)
        if (resp.status === 401) {
            const url = String(resource ?? '')
            if (!url.includes('/login') && !url.includes('/index')) {
                window.location.href = '/index.html'
            }
        }
        return resp
    }
})()

const TRANSLATIONS = {
  en: {
    'nav.myTrips': '✈ My Trips',
    'nav.groups': '🌍 Groups',
    'nav.feed': '📰 Feed',
    'nav.profile': '👤 Profile',
    'nav.settings': '⚙ Settings',
    'nav.newTrip': '+ New Trip',
    'nav.aiChat': '💬 AI Chat',
    'nav.signIn': 'Sign In',
    'nav.signUp': 'Sign Up',
    'footer': '© 2026 Diartrip — Intelligent Travel Planning',
    'index.hero.title': 'AI-Powered Travel Planning',
    'index.hero.subtitle': 'Discover personalized itineraries, amazing restaurants, local events and trip weather — All facilitated by AI.',
    'index.hero.cta': 'Plan my trip',
    'index.features.title': 'Features',
    'index.feat.ai.title': 'AI Itineraries',
    'index.feat.ai.desc': 'Automatic planning based on your travel style, dates and budget.',
    'index.feat.weather.title': 'Trip Weather',
    'index.feat.weather.desc': 'Check the weather forecast during your trip period.',
    'index.feat.restaurants.title': 'Recommended Restaurants',
    'index.feat.restaurants.desc': 'Discover the best restaurants rated by travelers.',
    'index.feat.events.title': 'Local Events & Tourist Spots',
    'index.feat.events.desc': 'Tourist spots, shows, festivals and events near your destination and all their details.',
    'index.feat.hotels.title': 'Ideal Hotels',
    'index.feat.hotels.desc': 'Find accommodations with strategic locations.',
    'index.feat.itinerary.title': 'Optimized Itinerary',
    'index.feat.itinerary.desc': 'The AI organizes tours avoiding unnecessary travel.',
    'index.feat.chat.title': 'AI Chat',
    'index.feat.chat.desc': 'Chat with the AI and get answers easily.',
    'index.feat.groups.title': 'Group Formation',
    'index.feat.groups.desc': 'Gather with your friends or family and discuss the best ideas to improve your trip.',
    'index.how.title': 'How it works',
    'index.how.step1': 'Enter destination, dates and preferences.',
    'index.how.step2': 'The AI analyzes weather, places and events.',
    'index.how.step3': 'Receive a complete itinerary ready to travel.',
    'index.reviews.title': 'What users say',
    'index.review1': '"I planned my entire trip in minutes. Incredible!"',
    'index.review2': '"The AI found restaurants I never would have discovered on my own."',
    'index.review3': '"Much better than searching everything manually."',
    'index.cta.title': 'Start planning your next adventure',
    'index.cta.subtitle': 'Discover the future of travel planning.',
    'index.cta.btn': 'Try Diartrip',
    'login.title': 'Login',
    'login.email.label': 'Email',
    'login.email.placeholder': 'Enter your email',
    'login.pass.label': 'Password',
    'login.pass.placeholder': 'Enter your password',
    'login.pass.show': 'show',
    'login.pass.hide': 'hide',
    'login.submit': 'Sign In',
    'login.noAccount': "Don't have an account? Click here.",
    'login.error': 'Could not log in, please try again.',
    'login.signingIn': 'Signing in...',
    'register.title': 'Sign Up',
    'register.name.label': 'Name',
    'register.name.placeholder': 'Enter your name',
    'register.email.label': 'Email',
    'register.email.placeholder': 'Enter your email',
    'register.pass.label': 'Password',
    'register.pass.placeholder': 'Create a password',
    'register.pass.hint': 'Minimum 8 characters, with at least one uppercase letter and one number.',
    'register.submit': 'Create Account',
    'register.hasAccount': 'Already have an account? Click here.',
    'register.creating': 'Creating...',
    'register.err.name': 'Name must be at least 3 characters.',
    'register.err.email': 'Invalid email.',
    'register.err.passLen': 'Password must be at least 8 characters.',
    'register.err.passUpper': 'Password must contain at least one uppercase letter.',
    'register.err.passNum': 'Password must contain at least one number.',
    'register.err.emailTaken': 'This email is already registered.',
    'register.err.create': 'Error creating account. Please try again.',
    'register.err.autoLogin': 'Account created, but automatic login failed.',
    'register.err.connect': 'Could not connect to server.',
    'lobby.greeting': 'Hello, ',
    'lobby.trips.heading': 'My Trips',
    'lobby.trips.section': 'Your trips',
    'lobby.trips.empty': 'No trips found.',
    'lobby.chat.header': 'Travel AI Assistant',
    'lobby.chat.initial': 'Hello! Select a trip and ask me anything about it.',
    'lobby.chat.placeholder': 'Ask something about your trip...',
    'lobby.chat.send': 'Send',
    'lobby.chat.selectFirst': 'Select a trip before sending a message.',
    'lobby.chat.typing': 'typing...',
    'lobby.chat.you': 'You',
    'lobby.chat.error': 'Error getting response.',
    'lobby.chat.noServer': 'Could not connect to server.',
    'lobby.chat.selected': 'selected! How can I help?',
    'common.loading': 'Loading...',
    'common.error': 'Error',
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.delete': 'Delete',
    'common.confirmDelete': 'Delete this item?',
    'common.success': 'Success!',
    'common.copy': 'Copy',
    'common.copied': 'Code copied!',
    'common.at': 'until',
    'formViagem.title': '+ New Trip',
    'formViagem.plan': 'Plan Trip ✈️',
    'formViagem.name': 'Trip name',
    'formViagem.name.placeholder': 'e.g. Europe Summer 2025',
    'formViagem.city': 'City',
    'formViagem.cityPlaceholder': 'e.g. Paris',
    'formViagem.start': 'Start date',
    'formViagem.end': 'End date',
    'formViagem.budget': 'Budget (R$)',
    'formViagem.type': 'Trip type',
    'formViagem.type.gastronomic': 'Gastronomic',
    'formViagem.type.adventure': 'Adventure',
    'formViagem.type.cultural': 'Cultural',
    'formViagem.type.relax': 'Relaxation',
    'formViagem.prefs.label': 'Preferences',
    'formViagem.prefs.placeholder': 'e.g. museums, restaurants...',
    'formViagem.submit': 'Generate Itinerary',
    'formViagem.generating': 'Itinerary being generated...',
    'formViagem.fillAll': 'Fill in all fields.',
    'formViagem.invalidBudget': 'Enter a valid budget (e.g. 3000.00).',
    'formViagem.invalidInfo': 'Invalid information',
    'formViagem.error': 'Error creating trip.',
    'formViagem.serverError': 'Error connecting to server.',
    'formViagem.success': 'Trip created successfully!',
    'feed.header': 'Feed',
    'feed.placeholder': 'Share something about your trip...',
    'feed.photo': '📷 Photo',
    'feed.publish': 'Publish',
    'feed.empty': 'No posts yet. Be the first! 🌍',
    'feed.date.now': 'just now',
    'feed.date.min': ' min ago',
    'feed.date.hour': ' h ago',
    'feed.date.days': ' days ago',
    'feed.confirmDelete': 'Delete this post?',
    'grupos.header': 'Groups',
    'grupos.joinTitle': '🔑 Join a group',
    'grupos.joinPlaceholder': 'Invite code (e.g. AB12CD)',
    'grupos.joinBtn': 'Join',
    'grupos.yourGroups': 'Your groups',
    'grupos.empty': 'You don\'t belong to any group yet.<br>Create a trip or enter with the code above.',
    'grupos.viewTrip': 'View trip',
    'grupos.chat': '💬 Chat',
    'grupos.enterCodeError': 'Enter the invite code.',
    'grupos.joinError': 'Error joining the group.',
    'perfil.edit': '✏️ Edit Profile',
    'perfil.save': 'Save',
    'perfil.cancel': 'Cancel',
    'perfil.name.label': 'Name',
    'perfil.bio.label': 'Bio',
    'perfil.bio.hint': '(max. 200 characters)',
    'perfil.bio.placeholder': 'Tell us a bit about yourself...',
    'perfil.config': '⚙ Account Settings',
    'perfil.notFound': 'Profile not found',
    'perfil.addBio': 'Add a bio...',
    'perfil.memberSince': 'Member since',
    'perfil.postsTitle': 'Posts',
    'perfil.emptyPosts': 'No posts yet.',
    'perfil.updated': 'Profile updated!',
    'perfil.saveError': 'Error saving.',
    'perfil.usePhoto': '✓ Use this photo',
    'perfil.confirmDeletePost': 'Delete this post?',
    'config.header': '⚙ Settings',
    'config.changeAccount': 'Change account information',
    'config.alterTitle': 'Change account information',
    'config.newName': 'New name',
    'config.newEmail': 'New email',
    'config.confirmPass': 'Confirm your password',
    'config.namePlaceholder': 'Your name',
    'config.emailPlaceholder': 'your@email.com',
    'config.passPlaceholder': 'Your password',
    'config.show': 'show',
    'config.hide': 'hide',
    'config.saveChanges': 'Save changes',
    'config.deleteAccount': 'Delete account',
    'config.updateSuccess': 'User updated successfully!',
    'config.updateError': 'An error occurred while updating the user. Try again.',
    'config.passMinLen': 'Password must be at least 6 characters.',
    'config.deleteSuccess': 'User deleted successfully!',
    'config.deleteError': 'An error occurred while deleting the user. Try again.',
    'viagem.copyCode': '📋 Copy invite code',
    'viagem.tab.overview': '📊 Overview',
    'viagem.tab.personal': '👤 My Finances',
    'viagem.tab.admin': '👑 Admin',
    'viagem.tab.expenses': '💸 Expenses',
    'viagem.tab.itinerary': '📋 Itinerary',
    'viagem.tab.chat': '💬 Chat',
    'viagem.tab.info': '📌 Info',
    'viagem.manageMembers': '👥 Manage Members',
    'viagem.registerExpense': '💸 Register Expense',
    'viagem.value': 'Value (R$)',
    'viagem.category': 'Category',
    'viagem.description': 'Description (optional)',
    'viagem.date': 'Date (optional)',
    'viagem.registerBtn': '+ Register expense',
    'viagem.history': 'Group history',
    'viagem.emptyExpenses': 'No expenses registered yet.',
    'viagem.itineraryTitle': '📋 Trip Itinerary',
    'viagem.addItem': 'Add item to itinerary',
    'viagem.itemTitle': 'Title (e.g.: Visit to Colosseum)',
    'viagem.itemDesc': 'Description (time, address, tips...)',
    'viagem.addBtn': '+ Add',
    'viagem.emptyItinerary': 'No items in the itinerary yet.',
    'viagem.groupChat': '💬 Group Chat',
    'viagem.chatPlaceholder': 'Type a message...',
    'viagem.infoTitle': '📌 Trip Information',
    'viagem.destination': 'Destination',
    'viagem.period': 'Period',
    'viagem.inviteCode': 'Invite code',
    'viagem.inviteTitle': '👥 Invite people',
    'viagem.inviteDesc': 'Share this code with your friends.',
    'viagem.aiAssistant': '🤖 AI Assistant',
    'viagem.aiUses': 'Use the AI chat in the lobby to ask for:',
    'viagem.aiFeature1': 'Personalized itineraries',
    'viagem.aiFeature2': 'Tourist spots',
    'viagem.aiFeature3': 'Restaurants',
    'viagem.aiFeature4': 'Saving tips',
    'viagem.aiFeature5': 'Weather and organization',
    'viagem.cat.transport': '🚗 Transport',
    'viagem.cat.food': '🍽️ Food',
    'viagem.cat.lodging': '🏨 Lodging',
    'viagem.cat.leisure': '🎭 Leisure',
    'viagem.cat.shopping': '🛍️ Shopping',
    'viagem.cat.health': '💊 Health',
    'viagem.cat.other': '📦 Other',
    'viagem.expenseError': 'Enter a valid value greater than zero.',
    'viagem.saving': 'Saving...',
    'viagem.confirmDeleteExpense': 'Delete this expense?',
    'viagem.errorLoad': 'Error loading trip',
    'viagem.badge.owner': '👑 Owner',
    'viagem.badge.admin': '⭐ Admin',
    'viagem.badge.member': 'Member',
    'viagem.action.promote': '⭐ Promote to Admin',
    'viagem.action.demote': 'Demote',
    'viagem.confirmPromote': 'Promote this user to administrator?',
    'viagem.confirmDemote': 'Demote this admin to a regular member?',
    'viagem.confirmDeleteRoteiro': 'Remove this item from the itinerary?',
    'viagem.errorPromote': 'Error promoting',
    'viagem.errorDemote': 'Error demoting',
    'viagem.itinerary.titleError': 'Enter a title.',
    'viagem.itinerary.edit': 'Edit',
    'viagem.itinerary.save': 'Save',
    'viagem.itinerary.cancel': 'Cancel',
    'viagem.tab.overview.dashboard': 'Group Dashboard',
    'viagem.tab.overview.budget': 'Budget',
    'viagem.tab.overview.totalSpent': 'Total Spent',
    'viagem.tab.overview.remaining': 'Remaining',
    'viagem.tab.overview.consumed': 'consumed',
    'viagem.tab.overview.categories': 'Categories',
    'viagem.tab.overview.noExpenses': 'No expenses registered',
    'viagem.tab.personal.myView': 'My View',
    'viagem.tab.personal.myFinances': 'My Finances',
    'viagem.tab.personal.paid': 'How much I paid',
    'viagem.tab.personal.debt': 'My debts',
    'viagem.tab.personal.recent': 'Last Expenses',
    'viagem.tab.personal.noRecent': 'No recent expenses',
    'viagem.tab.admin.panel': 'Administrative Panel',
    'viagem.tab.admin.ranking': 'Spending Ranking',
    'viagem.tab.admin.stats': 'Statistics',
    'viagem.tab.admin.activeMembers': 'Active Members',
    'viagem.tab.admin.photos': 'Group Photos',
    'viagem.tab.admin.itineraryItems': 'Itinerary Items',
  },
  'pt-BR': {
    'nav.myTrips': '✈ Minhas viagens',
    'nav.groups': '🌍 Grupos',
    'nav.feed': '📰 Feed',
    'nav.profile': '👤 Perfil',
    'nav.settings': '⚙ Configurações',
    'nav.newTrip': '+ Nova viagem',
    'nav.aiChat': '💬 Chat IA',
    'nav.signIn': 'Entrar',
    'nav.signUp': 'Cadastrar',
    'footer': '© 2026 Diartrip — Planejamento Inteligente de Viagens',
    'index.hero.title': 'Planejamento de viagens com Inteligência Artificial',
    'index.hero.subtitle': 'Descubra roteiros personalizados, restaurantes incríveis, eventos locais e clima da viagem — Tudo facilitado pela IA.',
    'index.hero.cta': 'Planejar minha viagem',
    'index.features.title': 'Funcionalidades',
    'index.feat.ai.title': 'Roteiros com IA',
    'index.feat.ai.desc': 'Planejamento automático baseado no seu estilo de viagem, datas e orçamento.',
    'index.feat.weather.title': 'Clima da viagem',
    'index.feat.weather.desc': 'Veja a previsão do tempo durante o período da viagem.',
    'index.feat.restaurants.title': 'Restaurantes recomendados',
    'index.feat.restaurants.desc': 'Descubra os melhores restaurantes avaliados por viajantes.',
    'index.feat.events.title': 'Eventos locais e pontos turísticos',
    'index.feat.events.desc': 'Pontos turístico, shows, festivais e eventos próximos ao seu destino e todos os seus detalhes.',
    'index.feat.hotels.title': 'Hotéis ideais',
    'index.feat.hotels.desc': 'Encontre hospedagens com localização estratégica.',
    'index.feat.itinerary.title': 'Roteiro otimizado',
    'index.feat.itinerary.desc': 'A IA organiza os passeios evitando deslocamentos desnecessários.',
    'index.feat.chat.title': 'Conversa com IA',
    'index.feat.chat.desc': 'Converse com a IA e tire dúvidas facilmente.',
    'index.feat.groups.title': 'Formação de grupos',
    'index.feat.groups.desc': 'Reuna-se com os seus amigos ou familiares e discuta as melhores ideias para melhorar a sua viagem.',
    'index.how.title': 'Como funciona',
    'index.how.step1': 'Informe destino, datas e preferências.',
    'index.how.step2': 'A IA analisa clima, lugares e eventos.',
    'index.how.step3': 'Receba um roteiro completo pronto para viajar.',
    'index.reviews.title': 'O que usuários dizem',
    'index.review1': '"Planejei minha viagem inteira em minutos. Incrível!"',
    'index.review2': '"A IA encontrou restaurantes que eu nunca teria descoberto sozinho."',
    'index.review3': '"Muito melhor que pesquisar tudo manualmente."',
    'index.cta.title': 'Comece a planejar sua próxima aventura',
    'index.cta.subtitle': 'Descubra o futuro do planejamento de viagens.',
    'index.cta.btn': 'Experimentar Diartrip',
    'login.title': 'Login',
    'login.email.label': 'Email',
    'login.email.placeholder': 'Digite seu email',
    'login.pass.label': 'Senha',
    'login.pass.placeholder': 'Digite sua senha',
    'login.pass.show': 'mostrar',
    'login.pass.hide': 'ocultar',
    'login.submit': 'Entrar',
    'login.noAccount': 'Não tem uma conta? Clique aqui.',
    'login.error': 'Não foi possível realizar o login, tente novamente.',
    'login.signingIn': 'Entrando...',
    'register.title': 'Cadastro',
    'register.name.label': 'Nome',
    'register.name.placeholder': 'Digite seu nome',
    'register.email.label': 'Email',
    'register.email.placeholder': 'Digite seu email',
    'register.pass.label': 'Senha',
    'register.pass.placeholder': 'Crie uma senha',
    'register.pass.hint': 'Mínimo 8 caracteres, com ao menos uma letra maiúscula e um número.',
    'register.submit': 'Criar conta',
    'register.hasAccount': 'Já tem uma conta? Clique aqui.',
    'register.creating': 'Criando...',
    'register.err.name': 'Nome deve ter pelo menos 3 caracteres.',
    'register.err.email': 'Email inválido.',
    'register.err.passLen': 'Senha deve ter no mínimo 8 caracteres.',
    'register.err.passUpper': 'A senha deve conter ao menos uma letra maiúscula.',
    'register.err.passNum': 'A senha deve conter ao menos um número.',
    'register.err.emailTaken': 'Este email já está cadastrado.',
    'register.err.create': 'Erro ao criar conta. Tente novamente.',
    'register.err.autoLogin': 'Conta criada, mas não foi possível fazer login automático.',
    'register.err.connect': 'Não foi possível conectar ao servidor.',
    'lobby.greeting': 'Olá, ',
    'lobby.trips.heading': 'Minhas viagens',
    'lobby.trips.section': 'Suas viagens',
    'lobby.trips.empty': 'Nenhuma viagem encontrada.',
    'lobby.chat.header': 'Assistente de Viagem IA',
    'lobby.chat.initial': 'Olá! Selecione uma viagem e pode me perguntar o que quiser sobre ela.',
    'lobby.chat.placeholder': 'Pergunte algo sobre sua viagem...',
    'lobby.chat.send': 'Enviar',
    'lobby.chat.selectFirst': 'Selecione uma viagem antes de enviar uma mensagem.',
    'lobby.chat.typing': 'digitando...',
    'lobby.chat.you': 'Você',
    'lobby.chat.error': 'Erro ao obter resposta.',
    'lobby.chat.noServer': 'Não foi possível conectar ao servidor.',
    'lobby.chat.selected': 'selecionada! Como posso ajudar?',
    'common.loading': 'Carregando...',
    'common.error': 'Erro',
    'common.save': 'Salvar',
    'common.cancel': 'Cancelar',
    'common.delete': 'Excluir',
    'common.confirmDelete': 'Excluir este item?',
    'common.success': 'Sucesso!',
    'common.copy': 'Copiar',
    'common.copied': 'Código copiado!',
    'common.at': 'até',
    'formViagem.title': '+ Nova viagem',
    'formViagem.plan': 'Planejar Viagem ✈️',
    'formViagem.name': 'Nome da viagem',
    'formViagem.name.placeholder': 'ex: Europa Verão 2025',
    'formViagem.city': 'Cidade',
    'formViagem.cityPlaceholder': 'ex: Paris',
    'formViagem.start': 'Data de início',
    'formViagem.end': 'Data de fim',
    'formViagem.budget': 'Orçamento (R$)',
    'formViagem.type': 'Tipo de viagem',
    'formViagem.type.gastronomic': 'Gastronômico',
    'formViagem.type.adventure': 'Aventura',
    'formViagem.type.cultural': 'Cultural',
    'formViagem.type.relax': 'Relaxamento',
    'formViagem.prefs.label': 'Preferências',
    'formViagem.prefs.placeholder': 'ex: museus, restaurantes...',
    'formViagem.submit': 'Gerar Roteiro',
    'formViagem.generating': 'Roteiro sendo gerado...',
    'formViagem.fillAll': 'Preencha todos os campos.',
    'formViagem.invalidBudget': 'Informe um orçamento válido (ex: 3000.00).',
    'formViagem.invalidInfo': 'Informações inválidas',
    'formViagem.error': 'Erro ao criar viagem.',
    'formViagem.serverError': 'Erro ao conectar com servidor.',
    'formViagem.success': 'Viagem criada com sucesso!',
    'feed.header': 'Feed',
    'feed.placeholder': 'Compartilhe algo sobre sua viagem...',
    'feed.photo': '📷 Foto',
    'feed.publish': 'Publicar',
    'feed.empty': 'Nenhum post ainda. Seja o primeiro! 🌍',
    'feed.date.now': 'agora mesmo',
    'feed.date.min': ' min atrás',
    'feed.date.hour': ' h atrás',
    'feed.date.days': ' dias atrás',
    'feed.confirmDelete': 'Excluir este post?',
    'grupos.header': 'Grupos',
    'grupos.joinTitle': '🔑 Entrar em um grupo',
    'grupos.joinPlaceholder': 'Código de convite (ex: AB12CD)',
    'grupos.joinBtn': 'Entrar',
    'grupos.yourGroups': 'Seus grupos',
    'grupos.empty': 'Você não pertence a nenhum grupo ainda.<br>Crie uma viagem ou entre pelo código acima.',
    'grupos.viewTrip': 'Ver viagem',
    'grupos.chat': '💬 Chat',
    'grupos.enterCodeError': 'Informe o código de convite.',
    'grupos.joinError': 'Erro ao entrar no grupo.',
    'perfil.edit': '✏️ Editar perfil',
    'perfil.save': 'Salvar',
    'perfil.cancel': 'Cancelar',
    'perfil.name.label': 'Nome',
    'perfil.bio.label': 'Bio',
    'perfil.bio.hint': '(máx. 200 caracteres)',
    'perfil.bio.placeholder': 'Conte um pouco sobre você...',
    'perfil.config': '⚙ Configurações da conta',
    'perfil.notFound': 'Perfil não encontrado',
    'perfil.addBio': 'Adicione uma bio...',
    'perfil.memberSince': 'Membro desde',
    'perfil.postsTitle': 'Postagens',
    'perfil.emptyPosts': 'Nenhuma postagem ainda.',
    'perfil.updated': 'Perfil atualizado!',
    'perfil.saveError': 'Erro ao salvar.',
    'perfil.usePhoto': '✓ Usar esta foto',
    'perfil.confirmDeletePost': 'Excluir este post?',
    'config.header': '⚙ Configurações',
    'config.changeAccount': 'Mudar informações da conta',
    'config.alterTitle': 'Alterar informações da conta',
    'config.newName': 'Novo nome',
    'config.newEmail': 'Novo email',
    'config.confirmPass': 'Confirme sua senha',
    'config.namePlaceholder': 'Seu nome',
    'config.emailPlaceholder': 'seu@email.com',
    'config.passPlaceholder': 'Sua senha',
    'config.show': 'mostrar',
    'config.hide': 'ocultar',
    'config.saveChanges': 'Salvar alterações',
    'config.deleteAccount': 'Excluir conta',
    'config.updateSuccess': 'Usuário atualizado com sucesso!',
    'config.updateError': 'Aconteceu algum erro ao atualizar o usuário. Tente novamente.',
    'config.passMinLen': 'A senha deve ter no mínimo 6 caracteres.',
    'config.deleteSuccess': 'Usuário deletado com sucesso!',
    'config.deleteError': 'Aconteceu algum erro ao deletar o usuário. Tente novamente.',
    'viagem.copyCode': '📋 Copiar código convite',
    'viagem.tab.overview': '📊 Visão Geral',
    'viagem.tab.personal': '👤 Meu Financeiro',
    'viagem.tab.admin': '👑 Admin',
    'viagem.tab.expenses': '💸 Gastos',
    'viagem.tab.itinerary': '📋 Roteiro',
    'viagem.tab.chat': '💬 Chat',
    'viagem.tab.info': '📌 Informações',
    'viagem.manageMembers': '👥 Gerenciar Membros',
    'viagem.registerExpense': '💸 Registrar Gasto',
    'viagem.value': 'Valor (R$)',
    'viagem.category': 'Categoria',
    'viagem.description': 'Descrição (opcional)',
    'viagem.date': 'Data (opcional)',
    'viagem.registerBtn': '+ Registrar gasto',
    'viagem.history': 'Histórico do grupo',
    'viagem.emptyExpenses': 'Nenhum gasto registrado ainda.',
    'viagem.itineraryTitle': '📋 Roteiro da Viagem',
    'viagem.addItem': 'Adicionar item ao roteiro',
    'viagem.itemTitle': 'Título (ex: Visita ao Coliseu)',
    'viagem.itemDesc': 'Descrição (horário, endereço, dicas...)',
    'viagem.addBtn': '+ Adicionar',
    'viagem.emptyItinerary': 'Nenhum item no roteiro ainda.',
    'viagem.groupChat': '💬 Chat do Grupo',
    'viagem.chatPlaceholder': 'Escreva uma mensagem...',
    'viagem.infoTitle': '📌 Informações da viagem',
    'viagem.destination': 'Destino',
    'viagem.period': 'Período',
    'viagem.inviteCode': 'Código convite',
    'viagem.inviteTitle': '👥 Convidar pessoas',
    'viagem.inviteDesc': 'Compartilhe este código com seus amigos.',
    'viagem.aiAssistant': '🤖 Assistente IA',
    'viagem.aiUses': 'Use o chat da IA no lobby para pedir:',
    'viagem.aiFeature1': 'Roteiros personalizados',
    'viagem.aiFeature2': 'Pontos turísticos',
    'viagem.aiFeature3': 'Restaurantes',
    'viagem.aiFeature4': 'Dicas de economia',
    'viagem.aiFeature5': 'Clima e organização',
    'viagem.cat.transport': '🚗 Transporte',
    'viagem.cat.food': '🍽️ Alimentação',
    'viagem.cat.lodging': '🏨 Hospedagem',
    'viagem.cat.leisure': '🎭 Lazer',
    'viagem.cat.shopping': '🛍️ Compras',
    'viagem.cat.health': '💊 Saúde',
    'viagem.cat.other': '📦 Outro',
    'viagem.expenseError': 'Informe um valor válido maior que zero.',
    'viagem.saving': 'Salvando...',
    'viagem.confirmDeleteExpense': 'Excluir este gasto?',
    'viagem.errorLoad': 'Erro ao carregar viagem',
    'viagem.badge.owner': '👑 Dono',
    'viagem.badge.admin': '⭐ Admin',
    'viagem.badge.member': 'Membro',
    'viagem.action.promote': '⭐ Promover a Admin',
    'viagem.action.demote': 'Rebaixar',
    'viagem.confirmPromote': 'Promover este usuário a administrador?',
    'viagem.confirmDemote': 'Rebaixar este admin para membro comum?',
    'viagem.confirmDeleteRoteiro': 'Remover este item do roteiro?',
    'viagem.errorPromote': 'Erro ao promover',
    'viagem.errorDemote': 'Erro ao rebaixar',
    'viagem.itinerary.titleError': 'Informe o título.',
    'viagem.itinerary.edit': 'Editar',
    'viagem.itinerary.save': 'Salvar',
    'viagem.itinerary.cancel': 'Cancelar',
    'viagem.tab.overview.dashboard': 'Dashboard do Grupo',
    'viagem.tab.overview.budget': 'Orçamento',
    'viagem.tab.overview.totalSpent': 'Total Gasto',
    'viagem.tab.overview.remaining': 'Restante',
    'viagem.tab.overview.consumed': 'consumido',
    'viagem.tab.overview.categories': 'Categorias',
    'viagem.tab.overview.noExpenses': 'Nenhum gasto registrado',
    'viagem.tab.personal.myView': 'Minha Visão',
    'viagem.tab.personal.myFinances': 'Meu Financeiro',
    'viagem.tab.personal.paid': 'Quanto eu paguei',
    'viagem.tab.personal.debt': 'Minhas dívidas',
    'viagem.tab.personal.recent': 'Últimos Gastos',
    'viagem.tab.personal.noRecent': 'Sem gastos recentes',
    'viagem.tab.admin.panel': 'Painel Administrativo',
    'viagem.tab.admin.ranking': 'Ranking de Gastos',
    'viagem.tab.admin.stats': 'Estatísticas',
    'viagem.tab.admin.activeMembers': 'Membros Ativos',
    'viagem.tab.admin.photos': 'Fotos no Grupo',
    'viagem.tab.admin.itineraryItems': 'Itens no Roteiro',
  }
}

const LANG_INFO = {
  en:      { fiClass: 'fi-us', code: 'EN' },
  'pt-BR': { fiClass: 'fi-br', code: 'BR' }
}

// Inject flag-icons CSS once
;(function injectFlagIcons() {
  if (document.getElementById('flag-icons-css')) return
  const link = document.createElement('link')
  link.id = 'flag-icons-css'
  link.rel = 'stylesheet'
  link.href = 'https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css'
  document.head.appendChild(link)
})()

function getLang() {
  return localStorage.getItem('diartrip_lang') || 'en'
}

function t(key) {
  const lang = getLang()
  return (TRANSLATIONS[lang] && TRANSLATIONS[lang][key]) || TRANSLATIONS['en'][key] || key
}

function applyTranslations() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.dataset.i18n)
  })
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    el.placeholder = t(el.dataset.i18nPlaceholder)
  })
  document.querySelectorAll('[data-i18n-value]').forEach(el => {
    el.value = t(el.dataset.i18nValue)
  })
}

function updateSelectorUI() {
  const lang = getLang()
  const info = LANG_INFO[lang]
  const flagEl = document.getElementById('i18nFlag')
  const codeEl = document.getElementById('i18nCode')
  if (flagEl) {
    flagEl.className = 'fi ' + info.fiClass
  }
  if (codeEl) codeEl.textContent = info.code
  document.querySelectorAll('.lang-option').forEach(btn => {
    btn.classList.toggle('lang-option--active', btn.dataset.lang === lang)
  })
}

function setLang(lang) {
  localStorage.setItem('diartrip_lang', lang)
  applyTranslations()
  updateSelectorUI()
  closeLangMenu()
  document.dispatchEvent(new CustomEvent('languageChanged', { detail: lang }))
}

function toggleLangMenu(e) {
  e.stopPropagation()
  const menu = document.getElementById('i18nMenu')
  if (menu) menu.classList.toggle('lang-menu--open')
}

function closeLangMenu() {
  const menu = document.getElementById('i18nMenu')
  if (menu) menu.classList.remove('lang-menu--open')
}

function buildSelector() {
  const el = document.createElement('div')
  el.className = 'lang-selector'
  el.id = 'langSelector'
  el.innerHTML =
    '<button class="lang-btn" id="i18nBtn" aria-label="Select language">' +
      '<span id="i18nFlag"></span>' +
      '<span id="i18nCode"></span>' +
      '<span class="lang-arrow">▾</span>' +
    '</button>' +
    '<div class="lang-menu" id="i18nMenu">' +
      '<button class="lang-option" data-lang="en" onclick="setLang(\'en\')"><span class="fi fi-us"></span> EN</button>' +
      '<button class="lang-option" data-lang="pt-BR" onclick="setLang(\'pt-BR\')"><span class="fi fi-br"></span> BR</button>' +
    '</div>'
  return el
}

function injectSelector() {
  const el = buildSelector()

  const userChip = document.getElementById('userChip')
  if (userChip) {
    userChip.parentNode.insertBefore(el, userChip)
  } else {
    const pubHeader = document.querySelector('header')
    if (pubHeader) {
      pubHeader.appendChild(el)
    } else {
      const appHeader = document.querySelector('.header')
      if (appHeader) {
        appHeader.appendChild(el)
      } else {
        el.classList.add('lang-selector--fixed')
        document.body.appendChild(el)
      }
    }
  }

  const btn = document.getElementById('i18nBtn')
  if (btn) btn.addEventListener('click', toggleLangMenu)
  document.addEventListener('click', closeLangMenu)
}

document.addEventListener('DOMContentLoaded', () => {
  injectSelector()
  updateSelectorUI()
  applyTranslations()
})
