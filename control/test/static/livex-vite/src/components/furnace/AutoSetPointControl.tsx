import type { AdapterEndpoint } from '@dssg/odin-react';
import type { FurnaceEndpointTypes } from '../../EndpointTypes';

import { TitleCard, WithEndpoint, EndpointInput, EndpointButton } from '@dssg/odin-react';
import { Form, Col, Row, FloatingLabel } from 'react-bootstrap';
import { checkNull, floatingInputStyle, floatingLabelStyle } from '../../utils';

const EndpointSelect = WithEndpoint(Form.Select);

interface AutoSetPointControlProps {
    furnaceEndPoint: AdapterEndpoint<FurnaceEndpointTypes>;
    connectedDisable: boolean;
}

function AutoSetPointControl(props: AutoSetPointControlProps){
    const {furnaceEndPoint, connectedDisable} = props;

    const heating_metadata = furnaceEndPoint.metadata?.autosp?.heating;

    return (
        <TitleCard
          title={
            <Row>
              <Col xs={3} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>Auto Set Point Control</Col>
              <Col xs={3}>
                <EndpointButton
                  endpoint={furnaceEndPoint}
                  fullpath="autosp/enable"
                  value={furnaceEndPoint.data?.autosp?.enable ? false : true}
                  variant={furnaceEndPoint.data?.autosp?.enable ? 'danger' : 'primary'}
                  >
                    {furnaceEndPoint.data?.autosp?.enable ? "Disable" : "Enable"}
                </EndpointButton>
              </Col>
            </Row>
          }>
          <Row>
            <Col xs={6} sm={4}>
              <FloatingLabel
              label="Rate (K/s)">
                <EndpointInput
                  endpoint={furnaceEndPoint}
                  fullpath="autosp/rate"
                  disabled={connectedDisable}
                />
              </FloatingLabel>
            </Col>
            <Col xs={6} sm={4}>
            <FloatingLabel
              label="Heat/Cool:">
                <EndpointSelect
                  endpoint={furnaceEndPoint}
                  fullpath="autosp/heating"
                  variant='outline-secondary'
                  buttonText={furnaceEndPoint.data?.autosp?.heating}
                  style={floatingInputStyle}
                  disabled={connectedDisable}>
                    {(heating_metadata?.allowed_values ?? []).map(
                      (selection, index) => (
                        <option value={selection} key={index}>
                          {selection}
                        </option>
                      )
                    )}
                </EndpointSelect>
            </FloatingLabel>
            </Col>
            <Col xs={6} sm={4}>
              <FloatingLabel
              label="Midpt. temp">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull(furnaceEndPoint.data?.autosp?.midpt_temp)}
                  />
              </FloatingLabel>

            </Col>
          </Row>
      </TitleCard>
    )
}

export default AutoSetPointControl;