import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import { DEFAULT_LANGUAGE } from "../config";

// Translation resources
const resources = {
  en: {
    translation: {
      // Common
      welcome: "Welcome back!",
      loading: "Loading...",
      save: "Save",
      cancel: "Cancel",
      delete: "Delete",
      edit: "Edit",
      create: "Create",
      search: "Search",
      filter: "Filter",
      export: "Export",
      import: "Import",
      
      // Navigation
      dashboard: "Dashboard",
      lessons: "Lessons",
      classes: "Classes",
      assessments: "Assessments",
      students: "Students",
      teachers: "Teachers",
      parents: "Parents",
      reports: "Reports",
      settings: "Settings",
      profile: "Profile",
      signOut: "Sign Out",
      
      // Roles
      admin: "Admin",
      teacher: "Teacher",
      student: "Student",
      parent: "Parent",
      
      // Dashboard
      totalXP: "Total XP",
      currentLevel: "Current Level",
      badges: "Badges",
      streakDays: "Streak Days",
      activeClasses: "Active Classes",
      todaysLessons: "Today's Lessons",
      averageProgress: "Average Progress",
      compliance: "Compliance",
      
      // Gamification
      xpGained: "+{{amount}} XP: {{reason}}",
      badgeEarned: "New badge earned: {{name}}",
      levelUp: "Level Up! You're now level {{level}}",
      leaderboard: "Leaderboard",
      rank: "Rank",
      
      // Messages
      successLessonCreated: "Lesson '{{title}}' created successfully",
      errorLessonCreation: "Failed to create lesson",
      successLessonDeleted: "Lesson deleted successfully",
      errorLessonDeletion: "Failed to delete lesson",
      confirmDelete: "Are you sure you want to delete '{{item}}'?",
      
      // Compliance
      coppaTitle: "COPPA Compliance",
      coppaDescription: "Children's Online Privacy Protection Act",
      ferpaTitle: "FERPA Compliance",
      ferpaDescription: "Family Educational Rights and Privacy Act",
      gdprTitle: "GDPR Compliance",
      gdprDescription: "General Data Protection Regulation",
      
      // Forms
      lessonTitle: "Lesson Title",
      lessonDescription: "Description",
      subject: "Subject",
      status: "Status",
      tags: "Tags",
      enableRobloxIntegration: "Enable Roblox Integration",
      
      // Actions
      pushToRoblox: "Push to Roblox",
      enterRobloxWorld: "Enter Roblox World",
      viewRewards: "View Rewards",
      createLesson: "Create Lesson",
      viewAssessments: "View Assessments",
      downloadReport: "Download Report",
      messageTeacher: "Message Teacher",
    },
  },
  es: {
    translation: {
      // Common
      welcome: "¡Bienvenido de nuevo!",
      loading: "Cargando...",
      save: "Guardar",
      cancel: "Cancelar",
      delete: "Eliminar",
      edit: "Editar",
      create: "Crear",
      search: "Buscar",
      filter: "Filtrar",
      export: "Exportar",
      import: "Importar",
      
      // Navigation
      dashboard: "Panel",
      lessons: "Lecciones",
      classes: "Clases",
      assessments: "Evaluaciones",
      students: "Estudiantes",
      teachers: "Profesores",
      parents: "Padres",
      reports: "Informes",
      settings: "Configuración",
      profile: "Perfil",
      signOut: "Cerrar sesión",
      
      // Roles
      admin: "Administrador",
      teacher: "Profesor",
      student: "Estudiante",
      parent: "Padre",
      
      // Dashboard
      totalXP: "XP Total",
      currentLevel: "Nivel Actual",
      badges: "Insignias",
      streakDays: "Días de Racha",
      activeClasses: "Clases Activas",
      todaysLessons: "Lecciones de Hoy",
      averageProgress: "Progreso Promedio",
      compliance: "Cumplimiento",
      
      // Gamification
      xpGained: "+{{amount}} XP: {{reason}}",
      badgeEarned: "Nueva insignia ganada: {{name}}",
      levelUp: "¡Subiste de nivel! Ahora eres nivel {{level}}",
      leaderboard: "Tabla de clasificación",
      rank: "Rango",
      
      // Messages
      successLessonCreated: "Lección '{{title}}' creada exitosamente",
      errorLessonCreation: "Error al crear la lección",
      successLessonDeleted: "Lección eliminada exitosamente",
      errorLessonDeletion: "Error al eliminar la lección",
      confirmDelete: "¿Estás seguro de que quieres eliminar '{{item}}'?",
      
      // Compliance
      coppaTitle: "Cumplimiento COPPA",
      coppaDescription: "Ley de Protección de la Privacidad Infantil en Internet",
      ferpaTitle: "Cumplimiento FERPA",
      ferpaDescription: "Ley de Derechos Educativos y Privacidad Familiar",
      gdprTitle: "Cumplimiento GDPR",
      gdprDescription: "Reglamento General de Protección de Datos",
      
      // Forms
      lessonTitle: "Título de la Lección",
      lessonDescription: "Descripción",
      subject: "Asignatura",
      status: "Estado",
      tags: "Etiquetas",
      enableRobloxIntegration: "Habilitar Integración con Roblox",
      
      // Actions
      pushToRoblox: "Enviar a Roblox",
      enterRobloxWorld: "Entrar al Mundo Roblox",
      viewRewards: "Ver Recompensas",
      createLesson: "Crear Lección",
      viewAssessments: "Ver Evaluaciones",
      downloadReport: "Descargar Informe",
      messageTeacher: "Mensaje al Profesor",
    },
  },
  fr: {
    translation: {
      // Common
      welcome: "Bienvenue!",
      loading: "Chargement...",
      save: "Enregistrer",
      cancel: "Annuler",
      delete: "Supprimer",
      edit: "Modifier",
      create: "Créer",
      search: "Rechercher",
      filter: "Filtrer",
      export: "Exporter",
      import: "Importer",
      
      // Navigation
      dashboard: "Tableau de bord",
      lessons: "Leçons",
      classes: "Classes",
      assessments: "Évaluations",
      students: "Étudiants",
      teachers: "Enseignants",
      parents: "Parents",
      reports: "Rapports",
      settings: "Paramètres",
      profile: "Profil",
      signOut: "Déconnexion",
      
      // Roles
      admin: "Administrateur",
      teacher: "Enseignant",
      student: "Étudiant",
      parent: "Parent",
      
      // Dashboard
      totalXP: "XP Total",
      currentLevel: "Niveau Actuel",
      badges: "Badges",
      streakDays: "Jours de Série",
      activeClasses: "Classes Actives",
      todaysLessons: "Leçons d'Aujourd'hui",
      averageProgress: "Progrès Moyen",
      compliance: "Conformité",
      
      // Gamification
      xpGained: "+{{amount}} XP: {{reason}}",
      badgeEarned: "Nouveau badge gagné: {{name}}",
      levelUp: "Niveau supérieur! Vous êtes maintenant niveau {{level}}",
      leaderboard: "Classement",
      rank: "Rang",
      
      // Messages
      successLessonCreated: "Leçon '{{title}}' créée avec succès",
      errorLessonCreation: "Échec de la création de la leçon",
      successLessonDeleted: "Leçon supprimée avec succès",
      errorLessonDeletion: "Échec de la suppression de la leçon",
      confirmDelete: "Êtes-vous sûr de vouloir supprimer '{{item}}'?",
      
      // Compliance
      coppaTitle: "Conformité COPPA",
      coppaDescription: "Loi sur la protection de la vie privée des enfants en ligne",
      ferpaTitle: "Conformité FERPA",
      ferpaDescription: "Loi sur les droits éducatifs et la confidentialité de la famille",
      gdprTitle: "Conformité RGPD",
      gdprDescription: "Règlement général sur la protection des données",
      
      // Forms
      lessonTitle: "Titre de la Leçon",
      lessonDescription: "Description",
      subject: "Matière",
      status: "Statut",
      tags: "Étiquettes",
      enableRobloxIntegration: "Activer l'intégration Roblox",
      
      // Actions
      pushToRoblox: "Envoyer vers Roblox",
      enterRobloxWorld: "Entrer dans le monde Roblox",
      viewRewards: "Voir les récompenses",
      createLesson: "Créer une leçon",
      viewAssessments: "Voir les évaluations",
      downloadReport: "Télécharger le rapport",
      messageTeacher: "Message à l'enseignant",
    },
  },
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: DEFAULT_LANGUAGE,
    fallbackLng: "en",
    interpolation: {
      escapeValue: false, // React already escapes values
    },
    react: {
      useSuspense: false,
    },
  });

export default i18n;