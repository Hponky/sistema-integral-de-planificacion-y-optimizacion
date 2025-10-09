export interface DemandData {
  date: string; // LocalDate en Java se puede representar como string en TypeScript
  timeInterval: string; // LocalTime en Java se puede representar como string en TypeScript
  expectedCalls: number; // Integer en Java se puede representar como number en TypeScript
  averageHandleTime: number; // Double en Java se puede representar como number en TypeScript
}