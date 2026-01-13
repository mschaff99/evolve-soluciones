# Evolve Soluciones - Frontend React

Frontend moderno construido con React 18, TypeScript, Redux Toolkit y Vite.

## 🚀 Tecnologías

- **React 18** - Framework UI
- **TypeScript** - Tipado estático
- **Redux Toolkit** - Manejo de estado
- **React Router v6** - Enrutamiento
- **Axios** - Cliente HTTP
- **Vite** - Build tool y dev server
- **React Toastify** - Notificaciones

## 📦 Instalación

```bash
# Instalar dependencias
npm install
```

## 🛠️ Desarrollo

```bash
# Iniciar servidor de desarrollo
npm run dev

# El frontend estará disponible en http://localhost:3000
```

## 🏗️ Build

```bash
# Compilar para producción
npm run build

# Preview de build de producción
npm run preview
```

## 📁 Estructura del Proyecto

```
frontend/
├── src/
│   ├── api/                 # Clientes y servicios de API
│   │   ├── client.ts       # Cliente Axios configurado
│   │   └── services/       # Servicios por dominio
│   ├── components/         # Componentes reutilizables
│   ├── pages/              # Páginas de la aplicación
│   ├── store/              # Redux store y slices
│   ├── styles/             # Estilos globales
│   ├── types/              # Definiciones TypeScript
│   ├── App.tsx             # Componente principal
│   └── main.tsx            # Entry point
├── index.html              # HTML base
├── package.json            # Dependencias
├── tsconfig.json           # Configuración TypeScript
└── vite.config.ts          # Configuración Vite
```

## 🔌 API Backend

El frontend se conecta al backend Flask en:
- Desarrollo: `http://localhost:5000/api/v1`
- Producción: Configurar en `.env.production`

## 🎨 Estilos

Los estilos mantienen la estética visual del sistema original con:
- Colores principales: Gradiente púrpura (#7A007B - #9B1B9E)
- CSS Variables para fácil personalización
- Diseño responsive mobile-first

## 🔐 Autenticación

- Autenticación JWT con tokens
- Refresh token automático
- Rutas protegidas con React Router
- Interceptores Axios para manejo de tokens

## 📝 Uso

### Login

```typescript
import { useAppDispatch } from '@/store/hooks';
import { login } from '@/store/slices/authSlice';

const dispatch = useAppDispatch();
await dispatch(login({ nombre_usuario, contrasena }));
```

### Llamadas a API

```typescript
import { authService } from '@/api/services/auth.service';

const usuario = await authService.getCurrentUser();
```

## 🚧 TODO

- [ ] Implementar más módulos (F29, Empresas, etc.)
- [ ] Agregar tests unitarios (Jest + React Testing Library)
- [ ] Mejorar componentes UI
- [ ] Agregar más páginas del sistema
- [ ] Implementar lazy loading de rutas
