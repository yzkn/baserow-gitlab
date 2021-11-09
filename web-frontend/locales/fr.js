export default {
  action: {
    upload: 'Envoyer',
    back: 'Retour',
    backToLogin: "Retour à l'identification",
    signUp: 'Créer un compte',
    signIn: "S'identifier",
    createNew: 'Nouveau',
    create: 'Créer',
    change: 'Changer',
    delete: 'Supprimer',
    rename: 'Renomer',
    add: 'Ajouter',
    makeChoice: 'Choisissez',
    cancel: 'Annuler',
    save: '@TODO',
    retry: '@TODO',
  },
  adminType: {
    settings: 'Paramètres',
  },
  applicationType: {
    database: 'Base de données',
  },
  settingType: {
    password: 'Mot de passe',
    tokens: "Jetons d'API",
  },
  userFileUploadType: {
    file: 'de mon appareil',
    url: "d'une URL",
  },
  field: {
    emailAddress: 'Adresse électronique',
  },
  error: {
    invalidEmail: 'Veuillez entrer une adresse électronique valide.',
    notMatchingPassword: 'Les mots de passe ne correspondent pas.',
    minLength: 'Un minimum de {min} caractères sont attendus ici.',
    maxLength: 'Un maximum de {max} caractères sont attendus ici.',
    minMaxLength:
      'Un minimum de {min} et un maximum def {max} caractères sont attendus ici.',
    requiredField: 'Ce champ est requis.',
  },
  permission: {
    admin: 'Admin',
    adminDescription: 'Peut configurer et éditer les groupes et applications.',
    member: 'Membre',
    memberDescription: 'Peut configurer et éditer les applications.',
  },
  fieldType: {
    singleLineText: 'Texte (une ligne)',
    longText: 'Texte long',
    linkToTable: 'Lien vers une table',
    number: 'Nombre',
    boolean: 'Booléen',
    date: 'Date',
    lastModified: 'Dernière modification',
    createdOn: 'Date de création',
    url: 'URL',
    email: 'Email',
    file: 'Fichier',
    singleSelect: 'Liste déroulante',
    phoneNumber: 'Téléphone',
    formula: 'Formule',
  },
  viewFilter: {
    contains: 'contient',
    containsNot: 'ne contient pas',
    filenameContains: 'nom du fichier contient',
    has: 'est',
    hasNot: "n'est pas",
    higherThan: 'plus grand que',
    is: 'est',
    isNot: "n'est pas",
    isEmpty: 'est vide',
    isNotEmpty: "n'est pas vide",
    isDate: 'est égal',
    isBeforeDate: 'est avant',
    isAfterDate: 'est après',
    isNotDate: 'est différent',
    isToday: "est aujourd'hui",
    inThisMonth: 'ce mois-ci',
    inThisYear: 'cette année',
    lowerThan: 'plus petit que',
  },
  viewType: {
    grid: 'Tableau',
    form: 'Formulaire',
  },
  trashType: {
    group: 'groupe',
    application: 'application',
    table: 'table',
    field: 'champ',
    row: 'ligne',
  },
  webhook: {
    request: '@TODO',
    response: '@TODO',
    status: {
      noStatus: '@TODO',
      statusOK: '@TODO',
      statusNotOK: '@TODO',
    },
    events: {
      rowCreated: '@TODO',
      rowUpdated: '@TODO',
      rowDeleted: '@TODO',
    },
  },
}
