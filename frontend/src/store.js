import { configureStore } from '@reduxjs/toolkit'
import complaintReducer from './slices/complaintSlice.js'

export const store = configureStore({
  reducer: {
    complaint: complaintReducer,
  },
})
