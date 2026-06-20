import {
  createContext,
  useState
} from "react";

export const PolicyContext =
  createContext();

export function PolicyProvider({
  children
}) {

  const [policyId,
    setPolicyId] =
      useState("1");

  return (
    <PolicyContext.Provider
      value={{
        policyId,
        setPolicyId
      }}
    >
      {children}
    </PolicyContext.Provider>
  );
}