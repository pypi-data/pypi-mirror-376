import React from 'react';

import { usePreferencesContext } from '@/contexts/PreferencesContext';
import logger from '@/logger';
/**
 * Custom hook that provides storage interface for react-resizable-panels
 * with debounced updates to reduce API calls when resizing panels
 * See example implementation here: https://react-resizable-panels.vercel.app/examples/external-persistence
 * Note that the custom storage interface must expose a synchronous getItem and setItem method.
 */

const DEBOUNCE_MS = 500;

// Name is set by the autosaveId prop in PanelGroup
const LAYOUT_NAME = 'react-resizable-panels:layout';
// Confusingly, the names are in alphabetical order, but the order of the sizes is set by the order prop
// in the respective Panel components
const DEFAULT_LAYOUT =
  '{"main,properties,sidebar":{"expandToSizes":{},"layout":[24,50,24]}}';
const DEFAULT_LAYOUT_SMALL_SCREENS =
  '{"main":{"expandToSizes":{},"layout":[100]}}';

// Layout keys for the two possible panel combinations
const WITH_PROPERTIES_AND_SIDEBAR = 'main,properties,sidebar';
const ONLY_SIDEBAR = 'main,sidebar';
const ONLY_PROPERTIES = 'main,properties';

export default function useLayoutPrefs() {
  const [showPropertiesDrawer, setShowPropertiesDrawer] =
    React.useState<boolean>(false);
  const [showSidebar, setShowSidebar] = React.useState(true);
  const { layout, handleUpdateLayout, isLayoutLoadedFromDB } =
    usePreferencesContext();

  const timerRef = React.useRef<number | null>(null);

  const debouncedUpdateLayout = React.useCallback(
    (newLayout: string) => {
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current);
      }

      timerRef.current = window.setTimeout(() => {
        handleUpdateLayout(newLayout).catch(error => {
          logger.debug('Failed to update layout:', error);
        });
        timerRef.current = null;
      }, DEBOUNCE_MS);
    },
    [handleUpdateLayout]
  );

  const togglePropertiesDrawer = () => {
    setShowPropertiesDrawer(prev => !prev);
  };

  const toggleSidebar = () => {
    setShowSidebar(prev => !prev);
  };

  // Initialize layouts from saved preferences
  React.useEffect(() => {
    if (!isLayoutLoadedFromDB) {
      return;
    } else if (layout === '') {
      // If screen is small, default to no sidebar or properties drawer
      if (window.innerWidth < 640) {
        setShowPropertiesDrawer(false);
        setShowSidebar(false);
        return;
      } else {
        // default layout for larger screens includes properties drawer
        setShowPropertiesDrawer(true);
      }
    } else {
      try {
        const parsedLayout = JSON.parse(layout);
        const panelGroupData = parsedLayout[LAYOUT_NAME];

        if (panelGroupData) {
          if (panelGroupData[WITH_PROPERTIES_AND_SIDEBAR]) {
            setShowPropertiesDrawer(true);
            setShowSidebar(true);
          } else if (panelGroupData[ONLY_SIDEBAR]) {
            setShowPropertiesDrawer(false);
            setShowSidebar(true);
          } else if (panelGroupData[ONLY_PROPERTIES]) {
            setShowPropertiesDrawer(true);
            setShowSidebar(false);
          } else if (panelGroupData.main) {
            setShowSidebar(false);
            setShowPropertiesDrawer(false);
          }
        }
      } catch (error) {
        logger.debug('Error parsing layout:', error);
      }
    }
  }, [layout, isLayoutLoadedFromDB]);

  const layoutPrefsStorage = React.useMemo(
    () => ({
      getItem(name: string): string {
        // Don't try to parse layout until it's loaded from the database
        if (!isLayoutLoadedFromDB) {
          logger.debug('Layout not loaded from DB yet, returning empty string');
          return '';
        }
        // If layout is empty, return default layout based on screen size
        if (layout === '') {
          if (window.innerWidth < 640) {
            logger.debug(
              'Layout is empty and screen is small, returning default layout',
              DEFAULT_LAYOUT_SMALL_SCREENS
            );
            return DEFAULT_LAYOUT_SMALL_SCREENS;
          } else {
            logger.debug(
              'Layout is empty, returning default layout',
              DEFAULT_LAYOUT
            );
            return DEFAULT_LAYOUT;
          }
        }

        try {
          const layoutObj = JSON.parse(layout);
          const storedLayout = JSON.stringify(layoutObj[name]);

          if (!storedLayout) {
            logger.debug('No stored layout found for name:', name);
            return '';
          } else {
            logger.debug('getItem returning storedLayout:', storedLayout);
            return storedLayout;
          }
        } catch (error) {
          logger.debug('Error getting layout item:', error);
          return '';
        }
      },
      setItem(name: string, value: string) {
        logger.debug('setItem called with name:', name, 'value:', value);
        if (!isLayoutLoadedFromDB) {
          logger.debug('Layout not loaded from DB yet');
          return;
        }
        if (value === null || value === undefined || value === '') {
          logger.debug('setItem called with empty value, ignoring');
          return;
        }

        try {
          const incomingLayout = JSON.parse(value);
          const incomingLayoutKeys = Object.keys(incomingLayout);
          logger.debug(
            'setItem called with name:',
            name,
            'parsed value:',
            incomingLayout
          );
          logger.debug(
            'Current showPropertiesDrawer state:',
            showPropertiesDrawer
          );
          logger.debug('Current showSidebar state:', showSidebar);
          let newLayoutObj = {};

          // Find key to use
          // If there is only one key, this is the first time the layout is being set and we can use the one key directly
          //If there are multiple keys, use the one that does not exist in the current layout
          let key = '';
          if (incomingLayoutKeys.length === 1) {
            key = incomingLayoutKeys[0];
          } else if (incomingLayoutKeys.length > 1) {
            const possibleKey = incomingLayoutKeys.find(
              key => !Object.keys(JSON.parse(layout)[LAYOUT_NAME]).includes(key)
            );
            key = possibleKey || '';
          }

          // The new layout should use the key that matches the current state of the properties panel
          if (
            key === WITH_PROPERTIES_AND_SIDEBAR &&
            showPropertiesDrawer &&
            showSidebar
          ) {
            newLayoutObj = {
              [name]: {
                [WITH_PROPERTIES_AND_SIDEBAR]:
                  incomingLayout[WITH_PROPERTIES_AND_SIDEBAR]
              }
            };
          } else if (
            key === ONLY_SIDEBAR &&
            !showPropertiesDrawer &&
            showSidebar
          ) {
            newLayoutObj = {
              [name]: {
                [ONLY_SIDEBAR]: incomingLayout[ONLY_SIDEBAR]
              }
            };
          } else if (
            key === ONLY_PROPERTIES &&
            showPropertiesDrawer &&
            !showSidebar
          ) {
            newLayoutObj = {
              [name]: {
                [ONLY_PROPERTIES]: incomingLayout[ONLY_PROPERTIES]
              }
            };
          } else if (key === 'main' && !showPropertiesDrawer && !showSidebar) {
            newLayoutObj = {
              [name]: {
                main: incomingLayout['main']
              }
            };
          } else {
            logger.debug('Invalid layout value:', value);
            return;
          }

          // Pass to debounce func, eventually preferences API
          // Note: setItem has to be synchronous for react-resizable-panels,
          // which is there's no await here even though handleUpdateLayout is async
          const newLayoutString = JSON.stringify(newLayoutObj);
          logger.debug('setting layout with newLayoutString:', newLayoutString);
          debouncedUpdateLayout(newLayoutString);
        } catch (error) {
          logger.debug('Error setting layout item:', error);
        }
      }
    }),
    [
      layout,
      debouncedUpdateLayout,
      isLayoutLoadedFromDB,
      showPropertiesDrawer,
      showSidebar
    ]
  );

  // Clean up the timer on unmount
  React.useEffect(() => {
    return () => {
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current);
      }
    };
  }, []);

  return {
    layoutPrefsStorage,
    showPropertiesDrawer,
    togglePropertiesDrawer,
    showSidebar,
    toggleSidebar
  };
}
